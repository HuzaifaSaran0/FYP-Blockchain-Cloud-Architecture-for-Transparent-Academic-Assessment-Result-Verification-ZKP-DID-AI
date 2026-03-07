from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from examination.urls import public_urlpatterns


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/exams/", include("examination.urls")),
    path("api/public/", include((public_urlpatterns, "public"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
