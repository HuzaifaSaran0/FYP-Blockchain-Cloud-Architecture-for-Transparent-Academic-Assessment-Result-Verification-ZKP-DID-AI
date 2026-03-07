from django.db import models


class BlockchainRecord(models.Model):
    RECORD_TYPE_CHOICES = [
        ("result_published", "Result Published"),
        ("exam_created", "Exam Created"),
        ("did_assigned", "DID Assigned"),
        ("hash_verified", "Hash Verified"),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ("verified", "Verified"),
        ("unverified", "Unverified"),
        ("tampered", "Tampered"),
    ]

    record_type = models.CharField(max_length=30, choices=RECORD_TYPE_CHOICES)
    related_student = models.CharField(max_length=150, blank=True, null=True)
    related_exam = models.CharField(max_length=255, blank=True, null=True)
    transaction_hash = models.CharField(max_length=255, unique=True)
    block_number = models.PositiveIntegerField(default=0)
    data_hash = models.CharField(max_length=255, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="unverified",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.record_type} — {self.transaction_hash[:16]}"


class DIDEntry(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("active", "Active"),
        ("revoked", "Revoked"),
    ]

    registration = models.OneToOneField(
        "examination.Registration",
        on_delete=models.CASCADE,
        related_name="did_entry",
    )
    did_string = models.CharField(max_length=255, unique=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="active",
    )
    document = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return self.did_string

    @property
    def student_name(self):
        return self.registration.full_name

    @property
    def cnic(self):
        return self.registration.cnic

    @property
    def exam_title(self):
        return self.registration.exam_title
