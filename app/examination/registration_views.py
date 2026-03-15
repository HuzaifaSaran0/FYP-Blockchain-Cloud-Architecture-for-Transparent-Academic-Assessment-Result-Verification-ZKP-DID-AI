import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Registration
from .serializers import (
    RegistrationSubmitSerializer,
    RegistrationListSerializer,
    RegistrationDetailSerializer,
    RegistrationRejectSerializer,
)
from blockchain_layer.utils import create_blockchain_record
from monitoring.utils import log_activity


def _generate_did() -> str:
    return f"did:acadchain:{uuid.uuid4().hex}"


def _build_did_document(did: str, exam_title: str) -> dict:
    return {
        "@context": "https://www.w3.org/ns/did/v1",
        "id": did,
        "controller": "did:acadchain:acadchain-authority",
        "authentication": f"{did}#keys-1",
        "linkedExam": exam_title,
        "resultHash": "",
        "issuedAt": timezone.now().isoformat(),
    }


class PublicRegistrationSubmitView(APIView):
    """
    POST /api/public/register/
    Public — no authentication required.
    Accepts multipart/form-data with image files and base64 face image.
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = RegistrationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()

        return Response(
            {
                "id": registration.id,
                "reference_number": registration.reference_number,
                "message": (
                    "Registration submitted successfully. "
                    "You will be notified after review."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class RegistrationListView(APIView):
    """
    GET /api/registrations/
    Admin — JWT required.
    Supports ?status= and ?search= query params.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Registration.objects.select_related("exam").all()

        status_filter = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()

        if status_filter:
            qs = qs.filter(status=status_filter)

        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(cnic__icontains=search)
                | Q(reference_number__icontains=search)
                | Q(email__icontains=search)
            )

        serializer = RegistrationListSerializer(qs, many=True)
        return Response(
            {"count": qs.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )


class RegistrationDetailView(APIView):
    """
    GET /api/registrations/{id}/
    Admin — JWT required. Returns full detail with image URLs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        registration = get_object_or_404(
            Registration.objects.select_related("exam"), pk=pk
        )
        serializer = RegistrationDetailSerializer(
            registration, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegistrationApproveView(APIView):
    """
    POST /api/registrations/{id}/approve/
    Admin — JWT required.
    Approves registration, generates DID, creates DIDEntry and BlockchainRecord.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        registration = get_object_or_404(
            Registration.objects.select_related("exam"), pk=pk
        )

        if registration.status != "pending":
            return Response(
                {
                    "detail": f"Registration is already '{registration.status}'. "
                    "Only pending registrations can be approved."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate DID
        did_string = _generate_did()
        exam_title = registration.exam.title if registration.exam else "N/A"

        # Update registration
        registration.status = "approved"
        registration.did = did_string
        registration.reviewed_at = timezone.now()
        registration.save(update_fields=["status", "did", "reviewed_at"])

        # Create DIDEntry with W3C document
        from blockchain_layer.models import DIDEntry
        did_document = _build_did_document(did_string, exam_title)
        DIDEntry.objects.create(
            registration=registration,
            did_string=did_string,
            document=did_document,
            verification_status="active",
        )

        # Create BlockchainRecord
        create_blockchain_record(
            record_type="did_assigned",
            related_student=registration.full_name,
            related_exam=exam_title,
            extra_data=f"{did_string}:{registration.cnic}",
        )

        # Log activity
        log_activity(
            action=f"Registration approved: {registration.full_name} "
            f"(REF: {registration.reference_number}) — DID assigned",
            performed_by=request.user.full_name,
            request=request,
        )

        serializer = RegistrationDetailSerializer(
            registration, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegistrationRejectView(APIView):
    """
    POST /api/registrations/{id}/reject/
    Admin — JWT required.
    Rejects registration with a mandatory reason.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        registration = get_object_or_404(
            Registration.objects.select_related("exam"), pk=pk
        )

        if registration.status != "pending":
            return Response(
                {
                    "detail": f"Registration is already '{registration.status}'. "
                    "Only pending registrations can be rejected."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegistrationRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        registration.status = "rejected"
        registration.rejection_reason = reason
        registration.reviewed_at = timezone.now()
        registration.save(update_fields=["status", "rejection_reason", "reviewed_at"])

        log_activity(
            action=f"Registration rejected: {registration.full_name} "
            f"(REF: {registration.reference_number}) — Reason: {reason}",
            performed_by=request.user.full_name,
            request=request,
        )

        detail_serializer = RegistrationDetailSerializer(
            registration, context={"request": request}
        )
        return Response(detail_serializer.data, status=status.HTTP_200_OK)
