from rest_framework import serializers
from django.utils import timezone
from .models import Exam, Registration, Result


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
