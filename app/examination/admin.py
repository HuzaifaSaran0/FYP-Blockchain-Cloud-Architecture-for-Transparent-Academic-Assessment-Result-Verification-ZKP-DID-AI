from django.contrib import admin
from .models import Exam, Registration, Result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "education_level",
        "date",
        "time",
        "venue",
        "status",
        "total_seats",
        "get_enrolled_count",
        "created_at",
    ]
    list_filter = ["status", "education_level"]
    search_fields = ["title", "venue"]
    ordering = ["-date"]
    readonly_fields = ["created_at", "get_enrolled_count"]

    fieldsets = (
        (None, {
            "fields": ("title", "education_level", "status")
        }),
        ("Schedule", {
            "fields": ("date", "time", "venue")
        }),
        ("Capacity", {
            "fields": ("total_seats", "get_enrolled_count")
        }),
        ("Details", {
            "fields": ("description", "created_at")
        }),
    )

    @admin.display(description="Enrolled")
    def get_enrolled_count(self, obj):
        return obj.enrolled_count
