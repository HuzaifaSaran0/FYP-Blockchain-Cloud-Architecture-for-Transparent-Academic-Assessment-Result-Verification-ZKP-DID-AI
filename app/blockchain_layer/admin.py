from django.contrib import admin
from .models import BlockchainRecord, DIDEntry


@admin.register(BlockchainRecord)
class BlockchainRecordAdmin(admin.ModelAdmin):
    list_display = [
        "record_type",
        "related_student",
        "related_exam",
        "get_short_tx_hash",
        "block_number",
        "verification_status",
        "timestamp",
    ]
    list_filter = ["record_type", "verification_status"]
    search_fields = ["related_student", "related_exam", "transaction_hash"]
    ordering = ["-timestamp"]
    readonly_fields = [
        "transaction_hash",
        "data_hash",
        "block_number",
        "timestamp",
    ]

    fieldsets = (
        ("Record Info", {
            "fields": ("record_type", "related_student", "related_exam")
        }),
        ("Blockchain Data", {
            "fields": (
                "transaction_hash",
                "data_hash",
                "block_number",
                "verification_status",
            )
        }),
        ("Timestamps", {
            "fields": ("timestamp",)
        }),
    )

    @admin.display(description="TX Hash")
    def get_short_tx_hash(self, obj):
        return f"{obj.transaction_hash[:16]}..."


@admin.register(DIDEntry)
class DIDEntryAdmin(admin.ModelAdmin):
    list_display = [
        "get_student_name",
        "get_cnic",
        "get_exam_title",
        "get_short_did",
        "verification_status",
        "assigned_at",
    ]
    list_filter = ["verification_status"]
    search_fields = [
        "did_string",
        "registration__full_name",
        "registration__cnic",
    ]
    ordering = ["-assigned_at"]
    readonly_fields = [
        "did_string",
        "assigned_at",
        "document",
        "get_student_name",
        "get_cnic",
        "get_exam_title",
    ]

    fieldsets = (
        ("Student", {
            "fields": ("get_student_name", "get_cnic", "get_exam_title")
        }),
        ("DID", {
            "fields": ("did_string", "verification_status", "assigned_at")
        }),
        ("W3C DID Document", {
            "fields": ("document",),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Student Name")
    def get_student_name(self, obj):
        return obj.registration.full_name

    @admin.display(description="CNIC")
    def get_cnic(self, obj):
        return obj.registration.cnic

    @admin.display(description="Exam")
    def get_exam_title(self, obj):
        return obj.exam_title

    @admin.display(description="DID")
    def get_short_did(self, obj):
        return f"{obj.did_string[:30]}..."
