from django.urls import path
from .result_views import (
    ResultListCreateView,
    ResultPublishView,
    StudentAnswerDetailView,
    PublicCertificateVerifyView,
)

urlpatterns = [
    path("", ResultListCreateView.as_view(), name="result-list-create"),
    path("<int:pk>/publish/", ResultPublishView.as_view(), name="result-publish"),
    path("<int:pk>/answers/", StudentAnswerDetailView.as_view(), name="result-answers"),
]

# Public — no auth
public_urlpatterns = [
    path("verify/", PublicCertificateVerifyView.as_view(), name="public-verify"),
]