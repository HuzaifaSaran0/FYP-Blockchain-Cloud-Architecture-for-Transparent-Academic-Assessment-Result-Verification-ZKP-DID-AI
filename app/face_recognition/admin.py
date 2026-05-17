from django.contrib import admin
from .models import CheckinLog, FaceEncoding


@admin.register(CheckinLog)
class CheckinLogAdmin(admin.ModelAdmin):
    list_display = [
        "get_student_name",
        "exam",
        "matched",
        "confidence_score",
        "attempted_at",
        "ip_address",
    ]
    list_filter = ["matched", "exam"]
    search_fields = ["registration__full_name"]
    ordering = ["-attempted_at"]
    readonly_fields = [
        "exam", "registration", "matched",
        "confidence_score", "attempted_at", "ip_address",
    ]

    @admin.display(description="Student Name")
    def get_student_name(self, obj):
        return obj.registration.full_name if obj.registration else "Unknown"


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ["get_student_name", "created_at"]
    readonly_fields = ["registration", "encoding_vector", "created_at"]
    ordering = ["-created_at"]

    @admin.display(description="Student Name")
    def get_student_name(self, obj):
        return obj.registration.full_name