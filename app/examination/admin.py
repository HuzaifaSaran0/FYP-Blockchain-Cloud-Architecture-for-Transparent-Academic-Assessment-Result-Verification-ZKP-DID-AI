from django.contrib import admin
from django.utils.html import format_html
from .models import Exam, Registration, Result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "education_level", "date", "time",
        "venue", "status", "total_seats", "get_enrolled_count", "created_at",
    ]
    list_filter = ["status", "education_level"]
    search_fields = ["title", "venue"]
    ordering = ["-date"]
    readonly_fields = ["created_at", "get_enrolled_count"]

    fieldsets = (
        (None, {"fields": ("title", "education_level", "status")}),
        ("Schedule", {"fields": ("date", "time", "venue")}),
        ("Capacity", {"fields": ("total_seats", "get_enrolled_count")}),
        ("Details", {"fields": ("description", "created_at")}),
    )

    @admin.display(description="Enrolled")
    def get_enrolled_count(self, obj):
        return obj.enrolled_count


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "id", "full_name", "cnic", "exam", "education_level",
        "status", "reference_number", "submitted_at",
    ]
    list_filter = ["status", "education_level", "exam"]
    search_fields = ["full_name", "cnic", "email", "reference_number"]
    ordering = ["-submitted_at"]
    readonly_fields = [
        "submitted_at", "reviewed_at", "reference_number",
        "did", "get_id_card_front_preview",
        "get_id_card_back_preview", "get_face_preview",
    ]

    fieldsets = (
        ("Personal", {
            "fields": (
                "full_name", "father_name", "cnic",
                "email", "phone", "education_level",
            )
        }),
        ("Exam", {"fields": ("exam",)}),
        ("Identity Documents", {
            "fields": (
                "get_id_card_front_preview",
                "get_id_card_back_preview",
                "get_face_preview",
            )
        }),
        ("Review", {
            "fields": (
                "status", "reference_number", "did",
                "rejection_reason", "submitted_at", "reviewed_at",
            )
        }),
    )

    @admin.display(description="ID Front")
    def get_id_card_front_preview(self, obj):
        if obj.id_card_front:
            return format_html(
                '<img src="{}" style="max-height:150px;border-radius:6px;" />',
                obj.id_card_front.url,
            )
        return "—"

    @admin.display(description="ID Back")
    def get_id_card_back_preview(self, obj):
        if obj.id_card_back:
            return format_html(
                '<img src="{}" style="max-height:150px;border-radius:6px;" />',
                obj.id_card_back.url,
            )
        return "—"

    @admin.display(description="Face")
    def get_face_preview(self, obj):
        if obj.face_image:
            return format_html(
                '<img src="{}" style="max-height:150px;border-radius:6px;" />',
                obj.face_image.url,
            )
        return "—"
