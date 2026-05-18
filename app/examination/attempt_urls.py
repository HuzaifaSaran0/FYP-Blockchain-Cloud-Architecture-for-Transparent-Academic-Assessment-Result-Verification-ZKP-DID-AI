from django.urls import path
from .attempt_views import ExamAttemptStartView, ExamAttemptSubmitView

urlpatterns = [
    path("start/", ExamAttemptStartView.as_view(), name="attempt-start"),
    path("submit/", ExamAttemptSubmitView.as_view(), name="attempt-submit"),
]