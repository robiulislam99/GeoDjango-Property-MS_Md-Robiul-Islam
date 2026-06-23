from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("properties/", views.property_search, name="property_search"),
    path("search/", views.property_search, name="property_search_query"),
    path("property/<slug:slug>/", views.property_detail, name="property_detail"),
    path("api/locations/autocomplete/", views.location_autocomplete, name="location_autocomplete"),
    path("api/search/semantic/", views.semantic_search_api, name="semantic_search_api"),
]