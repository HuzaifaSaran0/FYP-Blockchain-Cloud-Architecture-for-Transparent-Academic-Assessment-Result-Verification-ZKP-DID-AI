from rest_framework import serializers
from django.utils import timezone
from .models import Exam, Registration, Result
import base64
import uuid
import re
from django.core.files.base import ContentFile


class ExamListSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "education_level",
            "date",
            "time",
            "venue",
            "total_seats",
            "enrolled_count",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "enrolled_count"]


class ExamDetailSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "education_level",
            "date",
            "time",
            "venue",
            "total_seats",
            "enrolled_count",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "enrolled_count", "status"]

    def validate_date(self, value):
        # Only enforce future date on creation
        if self.instance is None and value < timezone.now().date():
            raise serializers.ValidationError(
                "Exam date cannot be in the past."
            )
        return value

    def validate_total_seats(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Total seats must be at least 1."
            )
        if value > 10000:
            raise serializers.ValidationError(
                "Total seats cannot exceed 10,000."
            )
        return value

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters."
            )
        return value.strip()

    def validate_venue(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Venue must be at least 3 characters."
            )
        return value.strip()


class ExamStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["upcoming", "ongoing", "completed"]
    )

    def validate_status(self, value):
        instance = self.context.get("instance")
        if not instance:
            return value

        current = instance.status
        allowed_transitions = {
            "upcoming": ["ongoing"],
            "ongoing": ["completed"],
            "completed": [],
        }

        if value not in allowed_transitions[current]:
            allowed = allowed_transitions[current]
            if allowed:
                raise serializers.ValidationError(
                    f"Cannot transition from '{current}' to '{value}'. "
                    f"Allowed: {allowed}."
                )
            else:
                raise serializers.ValidationError(
                    f"Exam is already '{current}'. No further transitions allowed."
                )
        return value


class PublicExamSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.IntegerField(read_only=True)
    remaining_seats = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "education_level",
            "date",
            "time",
            "venue",
            "total_seats",
            "enrolled_count",
            "remaining_seats",
            "description",
        ]

    def get_remaining_seats(self, obj) -> int:
        return obj.total_seats - obj.enrolled_count


# ─────────────────────────────────────────────
# REGISTRATION SERIALIZERS
# ─────────────────────────────────────────────

def decode_base64_image(base64_string: str, prefix: str = "face") -> ContentFile:
    """Decode a base64 image string (with or without data URI) into a Django ContentFile."""
    if not base64_string:
        raise serializers.ValidationError("Face image is required.")
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
        return ContentFile(image_data, name=filename)
    except Exception:
        raise serializers.ValidationError("Invalid base64 image data.")


class RegistrationSubmitSerializer(serializers.ModelSerializer):
    exam_id = serializers.IntegerField(write_only=True)
    face_image = serializers.CharField(write_only=True)

    class Meta:
        model = Registration
        fields = [
            "full_name", "father_name", "cnic", "email",
            "phone", "education_level", "exam_id",
            "id_card_front", "id_card_back", "face_image",
        ]
        extra_kwargs = {
            "id_card_front": {"required": True},
            "id_card_back": {"required": True},
        }

    def validate_cnic(self, value):
        pattern = r"^\d{5}-\d{7}-\d$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "CNIC format must be XXXXX-XXXXXXX-X (e.g. 35202-1234567-9)."
            )
        return value

    def validate_phone(self, value):
        pattern = r"^03\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone must be in format 03XXXXXXXXX."
            )
        return value

    def validate_id_card_front(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID card front image must be under 5MB.")
        return value

    def validate_id_card_back(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("ID card back image must be under 5MB.")
        return value

    def validate_exam_id(self, value):
        try:
            exam = Exam.objects.get(pk=value)
        except Exam.DoesNotExist:
            raise serializers.ValidationError("Exam not found.")

        if exam.status != "upcoming":
            raise serializers.ValidationError(
                "Registrations are only open for upcoming exams."
            )

        remaining = exam.total_seats - exam.enrolled_count
        if remaining <= 0:
            raise serializers.ValidationError(
                "This exam has no remaining seats."
            )

        return value

    def validate(self, attrs):
        exam_id = attrs.get("exam_id")
        cnic = attrs.get("cnic")
        email = attrs.get("email")

        if exam_id and cnic:
            if Registration.objects.filter(exam_id=exam_id, cnic=cnic).exists():
                raise serializers.ValidationError(
                    {"cnic": "A registration with this CNIC already exists for this exam."}
                )

        if exam_id and email:
            if Registration.objects.filter(exam_id=exam_id, email=email).exists():
                raise serializers.ValidationError(
                    {"email": "A registration with this email already exists for this exam."}
                )

        return attrs

    def create(self, validated_data):
            exam_id = validated_data.pop("exam_id")
            face_base64 = validated_data.pop("face_image") # This is now a string

            exam = Exam.objects.get(pk=exam_id)
            
            # This converts the string into a Django ContentFile
            face_file = decode_base64_image(face_base64, prefix="face")

            registration = Registration.objects.create(
                exam=exam,
                face_image=face_file, # Pass the decoded file here
                **validated_data,
            )
            return registration


class RegistrationListSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True, default=None)

    class Meta:
        model = Registration
        fields = [
            "id", "full_name", "cnic", "email", "phone",
            "education_level", "exam_title", "reference_number",
            "status", "did", "submitted_at",
        ]
        read_only_fields = fields


class RegistrationDetailSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True, default=None)
    id_card_front = serializers.SerializerMethodField()
    id_card_back = serializers.SerializerMethodField()
    face_image = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = [
            "id", "full_name", "father_name", "cnic", "email",
            "phone", "education_level", "exam_title",
            "reference_number", "status", "did",
            "id_card_front", "id_card_back", "face_image",
            "rejection_reason", "submitted_at", "reviewed_at",
        ]
        read_only_fields = fields

    def _build_absolute_url(self, request, path) -> str | None:
        if not path:
            return None
        if request:
            return request.build_absolute_uri(path.url)
        return path.url

    def get_id_card_front(self, obj) -> str | None:
        request = self.context.get("request")
        return self._build_absolute_url(request, obj.id_card_front)

    def get_id_card_back(self, obj) -> str | None:
        request = self.context.get("request")
        return self._build_absolute_url(request, obj.id_card_back)

    def get_face_image(self, obj) -> str | None:
        request = self.context.get("request")
        return self._build_absolute_url(request, obj.face_image)


class RegistrationApproveSerializer(serializers.Serializer):
    """Read-only — no input needed for approval."""
    pass


class RegistrationRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(
        min_length=5,
        error_messages={
            "required": "A rejection reason is required.",
            "min_length": "Reason must be at least 5 characters.",
        }
    )