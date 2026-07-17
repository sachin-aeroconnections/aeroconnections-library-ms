from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "connected"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "database": str(e)}, status=503)


urlpatterns = [
    path("health/", health_check),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("setup/", include("apps.setup.urls")),
    path("", include("apps.books.urls")),
    path("", include("apps.loans.urls")),
    path("borrowers/", include("apps.borrowers.urls")),
    path("", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
