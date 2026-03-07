import uuid
from django.db import models


class Exam(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    ]
    EDUCATION_CHOICES = [
        ("matric", "Matric"),
        ("intermediate", "Intermediate"),
        ("bachelors", "Bachelors"),
        ("masters", "Masters"),
    ]

    title = models.CharField(max_length=255)
    education_level = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=255)
    total_seats = models.PositiveIntegerField(default=100)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

    @property
    def enrolled_count(self):
        return self.registrations.filter(status="approved").count()


class Registration(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    EDUCATION_CHOICES = Exam.EDUCATION_CHOICES

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="registrations",
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150)
    cnic = models.CharField(max_length=15)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    education_level = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    id_card_front = models.ImageField(upload_to="id_cards/front/", null=True, blank=True)
    id_card_back = models.ImageField(upload_to="id_cards/back/", null=True, blank=True)
    face_image = models.ImageField(upload_to="faces/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference_number = models.CharField(max_length=30, unique=True, blank=True)
    did = models.CharField(max_length=255, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.full_name} — {self.exam}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"REF-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def exam_title(self):
        return self.exam.title if self.exam else None


class Result(models.Model):
    GRADE_CHOICES = [
        ("A+", "A+"), ("A", "A"), ("B", "B"),
        ("C", "C"), ("D", "D"), ("F", "F"),
    ]
    STATUS_CHOICES = [
        ("pass", "Pass"),
        ("fail", "Fail"),
    ]

    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="result",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results",
    )
    marks_obtained = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=100)
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    result_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, blank=True
    )
    certificate_id = models.CharField(max_length=50, unique=True, blank=True)
    result_hash = models.CharField(max_length=255, blank=True)
    blockchain_tx = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.registration.full_name} — {self.exam.title}"
