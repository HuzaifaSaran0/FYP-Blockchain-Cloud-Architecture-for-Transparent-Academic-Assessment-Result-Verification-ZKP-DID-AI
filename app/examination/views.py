from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Exam
from .serializers import (
    ExamListSerializer,
    ExamDetailSerializer,
    ExamStatusSerializer,
    PublicExamSerializer,
)
from monitoring.utils import log_activity


class ExamListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/exams/       — list all exams (admin)
    POST /api/exams/       — create new exam (admin)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ExamDetailSerializer
        return ExamListSerializer

    def get_queryset(self):
        qs = Exam.objects.all()
        status_filter = self.request.query_params.get("status")
        education_level = self.request.query_params.get("education_level")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if education_level:
            qs = qs.filter(education_level=education_level)

        return qs

    def perform_create(self, serializer):
        exam = serializer.save()
        log_activity(
            action=f"Exam created: {exam.title}",
            performed_by=self.request.user.full_name,
            request=self.request,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return with list serializer to include enrolled_count
        output = ExamListSerializer(serializer.instance)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ExamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/exams/{id}/  — retrieve exam (admin)
    PATCH  /api/exams/{id}/  — update exam (admin)
    DELETE /api/exams/{id}/  — delete exam (admin, upcoming only)
    """
    permission_classes = [IsAuthenticated]
    queryset = Exam.objects.all()
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.request.method in ["PATCH"]:
            return ExamDetailSerializer
        return ExamListSerializer

    def perform_update(self, serializer):
        exam = serializer.save()
        log_activity(
            action=f"Exam updated: {exam.title}",
            performed_by=self.request.user.full_name,
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        exam = self.get_object()
        if exam.status != "upcoming":
            raise ValidationError(
                {
                    "detail": f"Cannot delete an exam with status '{exam.status}'. "
                    "Only upcoming exams can be deleted."
                }
            )
        log_activity(
            action=f"Exam deleted: {exam.title}",
            performed_by=request.user.full_name,
            request=request,
        )
        exam.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExamStatusUpdateView(APIView):
    """
    PATCH /api/exams/{id}/status/  — transition exam status (admin)
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        serializer = ExamStatusSerializer(
            data=request.data,
            context={"instance": exam},
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        old_status = exam.status
        exam.status = new_status
        exam.save(update_fields=["status"])

        log_activity(
            action=f"Exam status changed: {exam.title} [{old_status} → {new_status}]",
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(ExamListSerializer(exam).data, status=status.HTTP_200_OK)


class PublicExamListView(generics.ListAPIView):
    """
    GET /api/public/exams/  — list available upcoming exams (public)
    """
    permission_classes = [AllowAny]
    serializer_class = PublicExamSerializer

    def get_queryset(self):
        qs = Exam.objects.filter(status="upcoming")
        education_level = self.request.query_params.get("education_level")
        if education_level:
            qs = qs.filter(education_level=education_level)

        # Only return exams with remaining seats
        available = [
            exam for exam in qs
            if exam.total_seats - exam.enrolled_count > 0
        ]
        return available
