import uuid
import hashlib
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Exam, Registration, Question, QuestionOption, StudentAnswer, Result
from face_recognition.models import ExamSession
from blockchain_layer.models import DIDEntry
from blockchain_layer.utils import create_blockchain_record
from monitoring.utils import log_activity


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _calculate_grade(percentage: float):
    if percentage >= 90:
        return "A+", "pass"
    elif percentage >= 80:
        return "A", "pass"
    elif percentage >= 70:
        return "B", "pass"
    elif percentage >= 60:
        return "C", "pass"
    elif percentage >= 50:
        return "D", "pass"
    else:
        return "F", "fail"


def _publish_result(result: Result, registration, exam):
    """Hash result data, create BlockchainRecord, update DIDEntry, mark published."""
    hash_input = (
        f"{registration.full_name}:{registration.cnic}:"
        f"{exam.title}:{result.marks_obtained}:"
        f"{result.total_marks}:{result.grade}"
    )
    result_hash = _sha256(hash_input)
    certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"

    blockchain_record = create_blockchain_record(
        record_type="result_published",
        related_student=registration.full_name,
        related_exam=exam.title,
        extra_data=f"{certificate_id}:{result_hash}",
    )

    # Update DIDEntry resultHash
    try:
        did_entry = registration.did_entry
        did_entry.document["resultHash"] = result_hash
        did_entry.document["certificateId"] = certificate_id
        did_entry.save(update_fields=["document"])
    except DIDEntry.DoesNotExist:
        pass

    result.result_hash = result_hash
    result.certificate_id = certificate_id
    result.blockchain_tx = blockchain_record.transaction_hash
    result.is_published = True
    result.published_at = timezone.now()
    result.save(update_fields=[
        "result_hash", "certificate_id", "blockchain_tx",
        "is_published", "published_at",
    ])

    return result, blockchain_record


class ExamAttemptStartView(APIView):
    """
    GET /api/attempt/start/?token=<exam_session_token>
    No JWT — token-based only.
    Returns exam questions without revealing correct answers.
    """
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        token = request.query_params.get("token", "").strip()

        if not token:
            return Response(
                {"detail": "token query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = ExamSession.objects.select_related(
                "registration", "exam"
            ).get(token=token)
        except ExamSession.DoesNotExist:
            return Response(
                {"detail": "Invalid session token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.is_used:
            return Response(
                {"detail": "This session token has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.is_expired:
            return Response(
                {"detail": "Session token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exam = session.exam
        registration = session.registration

        questions = exam.questions.prefetch_related("options").all()
        total_marks = sum(q.marks for q in questions)

        questions_data = []
        for q in questions:
            options = [
                {"id": opt.id, "text": opt.text, "order": opt.order}
                for opt in q.options.all()
            ]
            questions_data.append({
                "id": q.id,
                "text": q.text,
                "marks": q.marks,
                "order": q.order,
                "options": options,
            })

        return Response(
            {
                "exam_title": exam.title,
                "student_name": registration.full_name,
                "duration_minutes": exam.duration_minutes,
                "expires_at": session.expires_at,
                "total_questions": questions.count(),
                "total_marks": total_marks,
                "questions": questions_data,
            },
            status=status.HTTP_200_OK,
        )


class ExamAttemptSubmitView(APIView):
    """
    POST /api/attempt/submit/
    No JWT — token-based only.

    Body:
    {
        "token": "...",
        "answers": [
            {"question_id": 1, "selected_option_id": 2},
            ...
        ]
    }
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        token = request.data.get("token", "").strip()
        answers_data = request.data.get("answers", [])

        if not token:
            return Response(
                {"detail": "token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = ExamSession.objects.select_related(
                "registration", "exam"
            ).get(token=token)
        except ExamSession.DoesNotExist:
            return Response(
                {"detail": "Invalid session token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.is_used:
            return Response(
                {"detail": "This exam has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.is_expired:
            return Response(
                {"detail": "Session token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exam = session.exam
        registration = session.registration
        questions = list(exam.questions.prefetch_related("options").all())
        total_marks = sum(q.marks for q in questions)

        # Save each answer and calculate marks
        marks_obtained = 0
        for answer in answers_data:
            question_id = answer.get("question_id")
            selected_option_id = answer.get("selected_option_id")

            try:
                question = Question.objects.get(pk=question_id, exam=exam)
                selected_option = QuestionOption.objects.get(
                    pk=selected_option_id, question=question
                )
            except (Question.DoesNotExist, QuestionOption.DoesNotExist):
                continue

            is_correct = selected_option.is_correct
            if is_correct:
                marks_obtained += question.marks

            StudentAnswer.objects.update_or_create(
                registration=registration,
                exam=exam,
                question=question,
                defaults={
                    "selected_option": selected_option,
                    "is_correct": is_correct,
                },
            )

        # Calculate grade
        percentage = round((marks_obtained / total_marks * 100), 2) if total_marks > 0 else 0
        grade, result_status = _calculate_grade(percentage)

        # Create Result
        result = Result.objects.create(
            registration=registration,
            exam=exam,
            marks_obtained=marks_obtained,
            total_marks=total_marks,
            grade=grade,
            result_status=result_status,
            attempt_type="auto",
        )

        # Publish to blockchain
        result, blockchain_record = _publish_result(result, registration, exam)

        # Mark session as used
        session.is_used = True
        session.save(update_fields=["is_used"])

        log_activity(
            action=(
                f"Exam submitted: {registration.full_name} "
                f"(REF: {registration.reference_number}) "
                f"— {exam.title} — {marks_obtained}/{total_marks} ({grade})"
            ),
            performed_by=registration.full_name,
            request=request,
        )

        return Response(
            {
                "student_name": registration.full_name,
                "exam_title": exam.title,
                "marks_obtained": marks_obtained,
                "total_marks": total_marks,
                "percentage": percentage,
                "grade": grade,
                "result_status": result_status,
                "certificate_id": result.certificate_id,
                "result_hash": result.result_hash,
                "blockchain_tx": result.blockchain_tx,
                "message": "Exam submitted successfully. Result published to blockchain.",
            },
            status=status.HTTP_200_OK,
        )