from rest_framework import serializers
from .models import DIDEntry, BlockchainRecord


class DIDEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="registration.full_name", read_only=True)
    cnic = serializers.CharField(source="registration.cnic", read_only=True)
    exam_title = serializers.SerializerMethodField()   # ← change this
    linked_result_hash = serializers.SerializerMethodField()

    class Meta:
        model = DIDEntry
        fields = [
            "id",
            "student_name",
            "cnic",
            "did_string",
            "exam_title",
            "linked_result_hash",
            "verification_status",
            "assigned_at",
        ]

    def get_exam_title(self, obj):
        return obj.exam_title

    def get_linked_result_hash(self, obj):
        return obj.document.get("resultHash", "")


class DIDDocumentSerializer(serializers.ModelSerializer):
    context = serializers.SerializerMethodField()
    id = serializers.CharField(source="did_string", read_only=True)
    controller = serializers.SerializerMethodField()
    authentication = serializers.SerializerMethodField()
    linked_exam = serializers.SerializerMethodField()
    result_hash = serializers.SerializerMethodField()
    issued_at = serializers.SerializerMethodField()

    class Meta:
        model = DIDEntry
        fields = [
            "context",
            "id",
            "controller",
            "authentication",
            "linked_exam",
            "result_hash",
            "issued_at",
        ]

    def get_context(self, obj):
        return obj.document.get("@context", "https://www.w3.org/ns/did/v1")

    def get_controller(self, obj):
        return obj.document.get("controller", "did:acadchain:acadchain-authority")

    def get_authentication(self, obj):
        return obj.document.get("authentication", f"{obj.did_string}#keys-1")

    def get_linked_exam(self, obj):
        return obj.document.get("linkedExam", obj.exam_title)

    def get_result_hash(self, obj):
        return obj.document.get("resultHash", "")

    def get_issued_at(self, obj):
        return obj.document.get("issuedAt", obj.assigned_at.isoformat())


class BlockchainRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainRecord
        fields = [
            "id",
            "record_type",
            "related_student",
            "related_exam",
            "transaction_hash",
            "block_number",
            "data_hash",
            "verification_status",
            "timestamp",
        ]