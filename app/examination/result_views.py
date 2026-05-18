import uuid
import hashlib
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Registration, Exam, Result, StudentAnswer
from blockchain_layer.models import DIDEntry
from blockchain_layer.utils import create_blockchain_record
from monitoring.utils import log_activity
from .attempt_views import _publish_result, _calculate_grade


class ResultListCreateView(APIView):
    """
    GET  /api/results/         — list all results (admin)
    POST /api/results/         — manually create result for paper-based exam (admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Result.objects.select_related("registration", "exam").all()

        exam_id = request.query_params.get("exam_id")
        attempt_type = request.query_params.get("attempt_type")

        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        if attempt_type:
            qs = qs.filter(attempt_type=attempt_type)

        data = [
            {
                "id": r.id,
                "student_name": r.registration.full_name,
                "reference_number": r.registration.reference_number,
                "exam_title": r.exam.title,
                "exam_type": r.exam.exam_type,
                "marks_obtained": r.marks_obtained,
                "total_marks": r.total_marks,
                "grade": r.grade,
                "result_status": r.result_status,
                "attempt_type": r.attempt_type,
                "is_published": r.is_published,
                "certificate_id": r.certificate_id,
                "blockchain_tx": r.blockchain_tx,
                "published_at": r.published_at,
            }
            for r in qs
        ]
        return Response({"count": len(data), "results": data}, status=status.HTTP_200_OK)

    def post(self, request):
        registration_id = request.data.get("registration_id")
        marks_obtained = request.data.get("marks_obtained")
        total_marks = request.data.get("total_marks", 100)

        if not registration_id or marks_obtained is None:
            return Response(
                {"detail": "registration_id and marks_obtained are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = get_object_or_404(
            Registration.objects.select_related("exam"), pk=registration_id
        )

        if registration.exam.exam_type != "paper":
            return Response(
                {"detail": "Manual result entry is only allowed for paper-based exams."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if registration.status != "approved":
            return Response(
                {"detail": "Only approved registrations can have results entered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(registration, "result"):
            return Response(
                {"detail": "A result already exists for this registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        marks_obtained = int(marks_obtained)
        total_marks = int(total_marks)
        percentage = round((marks_obtained / total_marks * 100), 2) if total_marks > 0 else 0
        grade, result_status = _calculate_grade(percentage)

        result = Result.objects.create(
            registration=registration,
            exam=registration.exam,
            marks_obtained=marks_obtained,
            total_marks=total_marks,
            grade=grade,
            result_status=result_status,
            attempt_type="manual",
        )

        log_activity(
            action=(
                f"Manual result entered: {registration.full_name} "
                f"(REF: {registration.reference_number}) "
                f"— {registration.exam.title} — {marks_obtained}/{total_marks} ({grade})"
            ),
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(
            {
                "id": result.id,
                "student_name": registration.full_name,
                "exam_title": registration.exam.title,
                "marks_obtained": result.marks_obtained,
                "total_marks": result.total_marks,
                "grade": result.grade,
                "result_status": result.result_status,
                "attempt_type": result.attempt_type,
                "is_published": result.is_published,
                "message": "Result saved. Use publish endpoint to push to blockchain.",
            },
            status=status.HTTP_201_CREATED,
        )


class ResultPublishView(APIView):
    """
    POST /api/results/{id}/publish/
    Admin — JWT required.
    Works for both paper and computer results that are not yet published.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        result = get_object_or_404(
            Result.objects.select_related("registration", "exam"), pk=pk
        )

        if result.is_published:
            return Response(
                {"detail": "Result is already published to blockchain."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result, blockchain_record = _publish_result(
            result, result.registration, result.exam
        )

        log_activity(
            action=(
                f"Result published: {result.registration.full_name} "
                f"(REF: {result.registration.reference_number}) "
                f"— {result.exam.title} — CERT: {result.certificate_id}"
            ),
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(
            {
                "student_name": result.registration.full_name,
                "exam_title": result.exam.title,
                "marks_obtained": result.marks_obtained,
                "total_marks": result.total_marks,
                "grade": result.grade,
                "result_status": result.result_status,
                "certificate_id": result.certificate_id,
                "result_hash": result.result_hash,
                "blockchain_tx": result.blockchain_tx,
                "published_at": result.published_at,
                "message": "Result published to blockchain successfully.",
            },
            status=status.HTTP_200_OK,
        )


class StudentAnswerDetailView(APIView):
    """
    GET /api/results/{id}/answers/
    Admin — JWT required.
    Shows all attempted answers for a computer-based result.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        result = get_object_or_404(
            Result.objects.select_related("registration", "exam"), pk=pk
        )

        if result.attempt_type != "auto":
            return Response(
                {"detail": "Answer detail is only available for computer-based exam results."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers = StudentAnswer.objects.filter(
            registration=result.registration,
            exam=result.exam,
        ).select_related("question", "selected_option")

        answers_data = []
        for ans in answers:
            correct_option = ans.question.options.filter(is_correct=True).first()
            answers_data.append({
                "question_text": ans.question.text,
                "marks": ans.question.marks,
                "selected_option": ans.selected_option.text,
                "correct_option": correct_option.text if correct_option else None,
                "is_correct": ans.is_correct,
            })

        return Response(
            {
                "student_name": result.registration.full_name,
                "exam_title": result.exam.title,
                "marks_obtained": result.marks_obtained,
                "total_marks": result.total_marks,
                "grade": result.grade,
                "answers": answers_data,
            },
            status=status.HTTP_200_OK,
        )