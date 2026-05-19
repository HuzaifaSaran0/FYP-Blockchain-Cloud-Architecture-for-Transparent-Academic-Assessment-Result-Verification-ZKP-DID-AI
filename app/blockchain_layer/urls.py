from django.urls import path
from .views import (
    BlockchainRecordListView,
    BlockchainVerifyView,
    ZKPSimulateView,
    DIDListView,
    DIDDetailView,
)

urlpatterns = [
    path("records/", BlockchainRecordListView.as_view(), name="blockchain-records"),
    path("verify/<int:pk>/", BlockchainVerifyView.as_view(), name="blockchain-verify"),
    path("zkp-simulate/<int:pk>/", ZKPSimulateView.as_view(), name="zkp-simulate"),
    path("did/", DIDListView.as_view(), name="did-list"),
    path("did/<int:pk>/", DIDDetailView.as_view(), name="did-detail"),
]