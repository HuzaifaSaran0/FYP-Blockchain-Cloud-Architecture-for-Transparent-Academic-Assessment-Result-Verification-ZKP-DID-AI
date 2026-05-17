import uuid
import logging
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from examination.models import Exam, Registration
from .models import CheckinLog, ExamSession
from .face_utils import decode_base64_to_tempfile, verify_face, cleanup_tempfile
from monitoring.utils import log_activity


logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _log_checkin(exam, registration, matched, distance, ip):
    CheckinLog.objects.create(
        exam=exam,
        registration=registration if matched else None,
        matched=matched,
        confidence_score=round(1 - distance, 4) if matched else 0.0,
        ip_address=ip,
    )


def _create_exam_session(registration, exam) -> ExamSession:
    token = uuid.uuid4().hex
    expires_at = timezone.now() + timedelta(minutes=exam.duration_minutes)
    return ExamSession.objects.create(
        registration=registration,
        exam=exam,
        token=token,
        expires_at=expires_at,
    )


class FaceVerifyView(APIView):
    """
    POST /api/face/verify/

    Body (JSON):
    {
        "image":   "data:image/jpeg;base64,...",
        "exam_id": 1
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_b64 = request.data.get("image", "").strip()
        exam_id = request.data.get("exam_id")
        ip = _get_client_ip(request)

        if not image_b64:
            return Response(
                {"detail": "image field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not exam_id:
            return Response(
                {"detail": "exam_id field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exam = get_object_or_404(Exam, pk=exam_id)

        live_path = None
        try:
            live_path = decode_base64_to_tempfile(image_b64)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registrations = Registration.objects.filter(
            exam=exam,
            status="approved",
        ).exclude(face_image="")

        if not registrations.exists():
            cleanup_tempfile(live_path)
            _log_checkin(exam, None, False, 1.0, ip)
            return Response(
                {
                    "matched": False,
                    "student_name": None,
                    "registration_id": None,
                    "did": None,
                    "exam_title": exam.title,
                    "exam_type": exam.exam_type,
                    "reference_number": None,
                    "exam_session_token": None,
                    "expires_at": None,
                    "message": "No approved registrations found for this exam.",
                },
                status=status.HTTP_200_OK,
            )

        matched_registration = None
        best_distance = 1.0

        for reg in registrations:
            stored_path = reg.face_image.path
            try:
                result = verify_face(live_path, stored_path)
                if result["matched"]:
                    if result["distance"] < best_distance:
                        best_distance = result["distance"]
                        matched_registration = reg
            except ValueError as e:
                error_msg = str(e).lower()
                if "no face detected" in error_msg or "clearly visible" in error_msg:
                    cleanup_tempfile(live_path)
                    return Response(
                        {"detail": str(e)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                logger.warning(
                    f"Face verification skipped for reg {reg.id}: {e}"
                )
                continue

        cleanup_tempfile(live_path)

        if matched_registration:
            _log_checkin(exam, matched_registration, True, best_distance, ip)

            # ── Create session token for computer-based exams only ──
            exam_session_token = None
            expires_at = None

            if exam.exam_type == "computer":
                session = _create_exam_session(matched_registration, exam)
                exam_session_token = session.token
                expires_at = session.expires_at

            log_activity(
                action=(
                    f"Face check-in GRANTED: {matched_registration.full_name} "
                    f"(REF: {matched_registration.reference_number}) "
                    f"— Exam: {exam.title} [{exam.exam_type}]"
                ),
                performed_by=request.user.full_name,
                request=request,
            )

            return Response(
                {
                    "matched": True,
                    "student_name": matched_registration.full_name,
                    "registration_id": matched_registration.id,
                    "did": matched_registration.did,
                    "exam_title": exam.title,
                    "exam_type": exam.exam_type,
                    "reference_number": matched_registration.reference_number,
                    "exam_session_token": exam_session_token,
                    "expires_at": expires_at,
                    "message": "Identity verified. Entry granted.",
                },
                status=status.HTTP_200_OK,
            )

        # No match found
        _log_checkin(exam, None, False, 1.0, ip)

        log_activity(
            action=f"Face check-in DENIED — Exam: {exam.title} — No match found",
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(
            {
                "matched": False,
                "student_name": None,
                "registration_id": None,
                "did": None,
                "exam_title": exam.title,
                "exam_type": exam.exam_type,
                "reference_number": None,
                "exam_session_token": None,
                "expires_at": None,
                "message": "No matching student found. Entry denied.",
            },
            status=status.HTTP_200_OK,
        )


class CheckinLogListView(APIView):
    """
    GET /api/face/checkin-logs/
    JWT required.
    Optional query params: ?exam_id=1&matched=true
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CheckinLog.objects.select_related("exam", "registration").all()

        exam_id = request.query_params.get("exam_id")
        matched = request.query_params.get("matched")

        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        if matched is not None:
            qs = qs.filter(matched=matched.lower() == "true")

        data = [
            {
                "id": log.id,
                "exam_title": log.exam.title,
                "student_name": (
                    log.registration.full_name if log.registration else None
                ),
                "reference_number": (
                    log.registration.reference_number
                    if log.registration
                    else None
                ),
                "matched": log.matched,
                "confidence_score": log.confidence_score,
                "attempted_at": log.attempted_at,
                "ip_address": log.ip_address,
            }
            for log in qs
        ]

        return Response(
            {"count": len(data), "results": data},
            status=status.HTTP_200_OK,
        )