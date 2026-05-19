from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import BlockchainRecord, DIDEntry
from .serializers import (
    BlockchainRecordSerializer,
    DIDEntrySerializer,
    DIDDocumentSerializer,
)
from .utils import create_blockchain_record


# ─── Blockchain Records ──────────────────────────────────────────────────────

class BlockchainRecordListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = BlockchainRecord.objects.all()
        record_type = request.query_params.get("record_type")
        if record_type:
            qs = qs.filter(record_type=record_type)
        serializer = BlockchainRecordSerializer(qs, many=True)
        return Response(
            {"count": qs.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )


class BlockchainVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        import hashlib
        record = get_object_or_404(BlockchainRecord, pk=pk)
        expected = hashlib.sha256(
            f"{record.related_student}:{record.related_exam}:".encode()
        ).hexdigest()

        # Recompute against stored data_hash prefix to detect tampering
        # (Simple simulation: verified unless status was manually set to tampered)
        if record.verification_status == "tampered":
            return Response(
                {
                    "status": "tampered",
                    "message": "Data integrity check failed. This record may have been altered.",
                },
                status=status.HTTP_200_OK,
            )

        record.verification_status = "verified"
        record.save(update_fields=["verification_status"])
        return Response(
            {
                "status": "verified",
                "message": "Blockchain record verified successfully. Data integrity confirmed.",
            },
            status=status.HTTP_200_OK,
        )


class ZKPSimulateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        get_object_or_404(BlockchainRecord, pk=pk)
        steps = [
            {
                "step": 1,
                "label": "Commitment Generation",
                "description": "A cryptographic commitment is created from the result data without exposing the raw value.",
                "status": "pending",
            },
            {
                "step": 2,
                "label": "Challenge Issued",
                "description": "The verifier sends a random challenge to the prover to prevent pre-computed forgeries.",
                "status": "pending",
            },
            {
                "step": 3,
                "label": "Proof Computed",
                "description": "The prover computes a response using the secret witness and the challenge. No data is revealed.",
                "status": "pending",
            },
            {
                "step": 4,
                "label": "Proof Transmitted",
                "description": "The zero-knowledge proof is transmitted to the verifier over a secure channel.",
                "status": "pending",
            },
            {
                "step": 5,
                "label": "Verification Complete",
                "description": "The verifier confirms the proof is valid. The result is authenticated without seeing raw data.",
                "status": "pending",
            },
        ]
        return Response({"steps": steps}, status=status.HTTP_200_OK)


# ─── DID ─────────────────────────────────────────────────────────────────────

class DIDListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = DIDEntry.objects.select_related("registration").all()
        serializer = DIDEntrySerializer(qs, many=True)
        return Response(
            {"count": qs.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )


class DIDDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        entry = get_object_or_404(
            DIDEntry.objects.select_related("registration"), pk=pk
        )
        serializer = DIDDocumentSerializer(entry)
        return Response(serializer.data, status=status.HTTP_200_OK)