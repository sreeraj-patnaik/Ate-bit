from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.mobileapi.urls")),
    path("", include("apps.users.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.extraction.urls")),
    path("", include("apps.opportunities.urls")),
]
