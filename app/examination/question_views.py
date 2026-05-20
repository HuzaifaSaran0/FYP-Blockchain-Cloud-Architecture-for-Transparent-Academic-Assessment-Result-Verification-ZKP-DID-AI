from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404


from .models import Exam, Question
from .serializers import QuestionCreateSerializer, QuestionListSerializer
from monitoring.utils import log_activity


class QuestionListCreateView(APIView):
    """
    GET  /api/exams/{exam_id}/questions/  — list all questions for an exam
    POST /api/exams/{exam_id}/questions/  — add a question with options
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        questions = exam.questions.prefetch_related("options").all()
        serializer = QuestionListSerializer(questions, many=True)
        return Response(
            {"count": questions.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)

        if exam.exam_type != "computer":
            return Response(
                {"detail": "Questions can only be added to computer-based exams."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if exam.status != "upcoming":
            return Response(
                {"detail": f"Cannot add questions to an exam with status '{exam.status}'. Only upcoming exams can be modified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save(exam=exam)

        log_activity(
            action=f"Question added to exam: {exam.title} — Q{question.id}: {question.text[:40]}",
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(
            QuestionListSerializer(question).data,
            status=status.HTTP_201_CREATED,
        )


class QuestionRetrieveUpdateDestroyView(APIView):
    """
    GET    /api/exams/{exam_id}/questions/{id}/  — question detail
    PATCH  /api/exams/{exam_id}/questions/{id}/  — update question + options
    DELETE /api/exams/{exam_id}/questions/{id}/  — delete question
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_question(self, exam_id, question_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        question = get_object_or_404(Question, pk=question_id, exam=exam)
        return exam, question

    def get(self, request, exam_id, pk):
        exam, question = self._get_question(exam_id, pk)
        serializer = QuestionListSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, exam_id, pk):
        exam, question = self._get_question(exam_id, pk)

        if exam.status != "upcoming":
            return Response(
                {"detail": f"Cannot edit questions for an exam with status '{exam.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = QuestionCreateSerializer(
            question, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()

        log_activity(
            action=f"Question updated in exam: {exam.title} — Q{question.id}",
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(
            QuestionListSerializer(question).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, exam_id, pk):
        exam, question = self._get_question(exam_id, pk)

        if exam.status != "upcoming":
            return Response(
                {"detail": f"Cannot delete questions for an exam with status '{exam.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_text = question.text[:40]
        question.delete()

        log_activity(
            action=f"Question deleted from exam: {exam.title} — '{question_text}'",
            performed_by=request.user.full_name,
            request=request,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)