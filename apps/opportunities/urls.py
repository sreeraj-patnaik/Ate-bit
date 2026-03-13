from django.urls import path

from . import views

urlpatterns = [
    path("calendar/feed/<str:token>.ics", views.calendar_feed, name="calendar_feed"),
    path("opportunity/new", views.opportunity_create, name="opportunity_create"),
    path("opportunity/<int:pk>", views.opportunity_detail, name="opportunity_detail"),
    path("opportunity/<int:pk>/calendar", views.export_calendar_event, name="export_calendar_event"),
    path("opportunity/<int:pk>/note", views.add_note, name="add_note"),
    path("opportunity/<int:pk>/edit", views.opportunity_update, name="opportunity_update"),
    path("opportunity/<int:pk>/delete", views.opportunity_delete, name="opportunity_delete"),
    path("opportunity/<int:pk>/toggle-save", views.toggle_saved, name="toggle_saved"),
    path("saved", views.saved_opportunities, name="saved_opportunities"),
]
