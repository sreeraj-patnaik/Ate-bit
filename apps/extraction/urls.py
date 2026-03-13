from django.urls import path

from . import views

urlpatterns = [
    path("submit", views.submit_opportunity, name="submit_opportunity"),
]
