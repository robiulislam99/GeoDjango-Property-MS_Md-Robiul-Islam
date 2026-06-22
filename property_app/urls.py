from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.property_search, name="property_search"),
    path("property/<slug:slug>/", views.property_detail, name="property_detail"),
    path("api/locations/autocomplete/", views.location_autocomplete, name="location_autocomplete"),
]