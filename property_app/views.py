from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from .models import Location, Property


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


def property_search(request):
    location_query = request.GET.get("location", "").strip()
    property_type = request.GET.get("type", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    bedrooms = request.GET.get("bedrooms", "").strip()

    properties = Property.objects.filter(is_active=True).select_related("location")

    if location_query:
        properties = properties.filter(
            Q(location__city__icontains=location_query)
            | Q(location__state__icontains=location_query)
            | Q(location__country__icontains=location_query)
            | Q(location__name__icontains=location_query)
        )
    if property_type:
        properties = properties.filter(property_type=property_type)
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if bedrooms:
        properties = properties.filter(bedrooms__gte=bedrooms)

    properties = properties.order_by("-is_featured", "-created_at")
    paginator = Paginator(properties, 9)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "property_app/search_results.html", {
        "page_obj": page_obj,
        "location_query": location_query,
        "total_results": paginator.count,
    })


def property_detail(request, slug):
    property_obj = get_object_or_404(
        Property.objects.select_related("location").prefetch_related("images", "amenities"),
        slug=slug,
        is_active=True,
    )

    distance_km = None
    if property_obj.point and property_obj.location.point:
        annotated = (
            Property.objects.filter(pk=property_obj.pk)
            .annotate(distance=Distance("point", property_obj.location.point))
            .first()
        )
        if annotated and annotated.distance is not None:
            distance_km = round(annotated.distance.km, 2)

    return render(request, "property_app/property_detail.html", {
        "property": property_obj,
        "distance_km": distance_km,
    })