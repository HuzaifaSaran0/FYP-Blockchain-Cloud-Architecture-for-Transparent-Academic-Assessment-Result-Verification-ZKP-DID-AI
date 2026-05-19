from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from examination.urls import public_urlpatterns as exam_public_urls
from examination.registration_views import PublicRegistrationSubmitView

public_patterns = exam_public_urls + [
    path(
        "register/",
        PublicRegistrationSubmitView.as_view(),
        name="public-register",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/exams/", include("examination.urls")),
    path("api/exams/<int:exam_id>/questions/", include("examination.question_urls")),
    path("api/registrations/", include("examination.registration_urls")),
    path("api/results/", include("examination.result_urls")),
    path("api/attempt/", include("examination.attempt_urls")),
    path("api/face/", include("face_recognition.urls")),
    path("api/public/", include((public_patterns, "public"))),
    path("api/monitoring/", include("monitoring.urls")),
    path("api/blockchain/", include("blockchain_layer.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)