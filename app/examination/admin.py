from django.contrib import admin
from django.utils.html import format_html
from .models import Exam, Registration, Result, Question, QuestionOption, StudentAnswer


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "education_level", "date", "time",
        "venue", "exam_type", "duration_minutes",
        "status", "total_seats", "get_enrolled_count", "created_at",
    ]
    list_filter = ["status", "education_level", "exam_type"]
    search_fields = ["title", "venue"]
    ordering = ["-date"]
    readonly_fields = ["created_at", "get_enrolled_count"]

    fieldsets = (
        (None, {"fields": ("title", "education_level", "status")}),
        ("Schedule", {"fields": ("date", "time", "venue")}),
        ("Exam Type", {"fields": ("exam_type", "duration_minutes")}),
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

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 2
    min_num = 2
    max_num = 5
    fields = ["text", "is_correct", "order"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "get_short_text", "exam", "marks", "order", "get_option_count", "created_at"]
    list_filter = ["exam"]
    search_fields = ["text"]
    ordering = ["exam", "order", "id"]
    readonly_fields = ["created_at"]
    inlines = [QuestionOptionInline]

    @admin.display(description="Question")
    def get_short_text(self, obj):
        return obj.text[:60]

    @admin.display(description="Options")
    def get_option_count(self, obj):
        return obj.options.count()


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "text", "is_correct", "order"]
    list_filter = ["is_correct", "question__exam"]
    search_fields = ["text"]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_student_name", "get_exam_title", "marks_obtained",
        "total_marks", "grade", "result_status", "attempt_type",
        "is_published", "published_at",
    ]
    list_filter = ["result_status", "grade", "is_published", "attempt_type", "exam"]
    search_fields = ["registration__full_name", "certificate_id"]
    readonly_fields = [
        "grade", "result_status", "certificate_id",
        "result_hash", "blockchain_tx", "is_published", "published_at",
    ]

    @admin.display(description="Student")
    def get_student_name(self, obj):
        return obj.registration.full_name

    @admin.display(description="Exam")
    def get_exam_title(self, obj):
        return obj.exam.title


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_student_name", "get_exam_title",
        "get_question_short", "get_selected_option", "is_correct", "answered_at",
    ]
    list_filter = ["is_correct", "exam"]
    search_fields = ["registration__full_name"]
    readonly_fields = fields = [
        "registration", "exam", "question",
        "selected_option", "is_correct", "answered_at",
    ]

    @admin.display(description="Student")
    def get_student_name(self, obj):
        return obj.registration.full_name

    @admin.display(description="Exam")
    def get_exam_title(self, obj):
        return obj.exam.title

    @admin.display(description="Question")
    def get_question_short(self, obj):
        return obj.question.text[:40]

    @admin.display(description="Selected")
    def get_selected_option(self, obj):
        return obj.selected_option.text