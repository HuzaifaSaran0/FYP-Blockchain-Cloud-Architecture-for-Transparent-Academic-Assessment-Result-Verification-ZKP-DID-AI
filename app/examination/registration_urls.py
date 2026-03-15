from django.urls import path
from .registration_views import (
    RegistrationListView,
    RegistrationDetailView,
    RegistrationApproveView,
    RegistrationRejectView,
)

urlpatterns = [
    path("", RegistrationListView.as_view(), name="registration-list"),
    path("<int:pk>/", RegistrationDetailView.as_view(), name="registration-detail"),
    path("<int:pk>/approve/", RegistrationApproveView.as_view(), name="registration-approve"),
    path("<int:pk>/reject/", RegistrationRejectView.as_view(), name="registration-reject"),
]
