from django.urls import path
from .views import (
    ExamListCreateView,
    ExamRetrieveUpdateDestroyView,
    ExamStatusUpdateView,
    PublicExamListView,
)

# Admin exam endpoints
urlpatterns = [
    path("", ExamListCreateView.as_view(), name="exam-list-create"),
    path("<int:pk>/", ExamRetrieveUpdateDestroyView.as_view(), name="exam-detail"),
    path("<int:pk>/status/", ExamStatusUpdateView.as_view(), name="exam-status"),
]

# Public exam endpoints (imported separately in core/urls.py)
public_urlpatterns = [
    path("exams/", PublicExamListView.as_view(), name="public-exam-list"),
]
