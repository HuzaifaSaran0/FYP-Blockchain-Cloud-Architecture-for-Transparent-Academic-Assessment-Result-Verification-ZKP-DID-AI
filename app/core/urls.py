from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from examination.urls import public_urlpatterns as exam_public_urls
from examination.registration_urls import urlpatterns as reg_urls

# Combine all public-facing patterns under /api/public/
public_patterns = exam_public_urls + [
    path(
        "register/",
        __import__(
            "examination.registration_views",
            fromlist=["PublicRegistrationSubmitView"],
        ).PublicRegistrationSubmitView.as_view(),
        name="public-register",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/exams/", include("examination.urls")),
    path("api/registrations/", include("examination.registration_urls")),
    path("api/public/", include((public_patterns, "public"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
