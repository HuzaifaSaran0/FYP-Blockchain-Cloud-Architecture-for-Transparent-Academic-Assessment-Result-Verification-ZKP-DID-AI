from django.urls import path
from .views import (
    ExportBlockchainView,
    ExportRegistrationsView,
    ExportResultsView,
    ExportAlertsView,
)

urlpatterns = [
    path("blockchain/", ExportBlockchainView.as_view(), name="export-blockchain"),
    path("registrations/", ExportRegistrationsView.as_view(), name="export-registrations"),
    path("results/", ExportResultsView.as_view(), name="export-results"),
    path("alerts/", ExportAlertsView.as_view(), name="export-alerts"),
]