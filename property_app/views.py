from django.shortcuts import render
from django.http import JsonResponse
from .models import Location


def home(request):
    return render(request, "property_app/home.html")


def location_autocomplete(request):
    query = request.GET.get("q", "").strip()
    results = []
    if len(query) >= 2:
        locations = Location.objects.filter(
            name__icontains=query, is_active=True
        )[:8]
        results = [
            {
                "id": loc.id,
                "label": f"{loc.city}, {loc.state}, {loc.country}" if loc.state else f"{loc.city}, {loc.country}",
                "slug": loc.slug,
            }
            for loc in locations
        ]
    return JsonResponse({"results": results})