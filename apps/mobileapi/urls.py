from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="api_register"),
    path("auth/token", TokenObtainPairView.as_view(), name="api_token_obtain_pair"),
    path("auth/token/refresh", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("profile", views.ProfileView.as_view(), name="api_profile"),
    path("opportunities", views.OpportunityListCreateView.as_view(), name="api_opportunities"),
    path("opportunities/extract", views.ExtractOpportunityView.as_view(), name="api_extract_opportunity"),
    path("opportunities/<int:pk>", views.OpportunityDetailView.as_view(), name="api_opportunity_detail"),
    path("opportunities/<int:pk>/notes", views.AddNoteView.as_view(), name="api_add_note"),
    path("timeline", views.TimelineView.as_view(), name="api_timeline"),
    path("devices", views.DeviceTokenView.as_view(), name="api_device_token"),
]
