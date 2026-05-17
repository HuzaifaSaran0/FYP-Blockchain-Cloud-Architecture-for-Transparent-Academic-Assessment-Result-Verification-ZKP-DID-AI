from django.urls import path
from .views import FaceVerifyView, CheckinLogListView

urlpatterns = [
    path("verify/", FaceVerifyView.as_view(), name="face-verify"),
    path("checkin-logs/", CheckinLogListView.as_view(), name="checkin-logs"),
]