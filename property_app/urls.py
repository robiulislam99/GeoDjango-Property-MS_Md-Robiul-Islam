from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/locations/autocomplete/", views.location_autocomplete, name="location_autocomplete"),
]