from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from pgvector.django import CosineDistance
from .models import Location, Property
from .semantic_search import semantic_property_search, get_model


def home(request):
    featured = Property.objects.filter(
        is_active=True, is_featured=True
    ).select_related("location").prefetch_related("images")[:4]

    if not featured.exists():
        featured = Property.objects.filter(
            is_active=True
        ).select_related("location").prefetch_related("images").order_by("-created_at")[:4]

    return render(request, "property_app/home.html", {"featured": featured})


def location_autocomplete(request):
    query = request.GET.get("q", "").strip()
    results = []
    if len(query) >= 2:
        locations = Location.objects.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(state__icontains=query),
            is_active=True
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
    # Single unified search field
    query = request.GET.get("q", "").strip()
    property_type = request.GET.get("type", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    bedrooms = request.GET.get("bedrooms", "").strip()

    properties = Property.objects.filter(
        is_active=True
    ).select_related("location").prefetch_related("images", "amenities")

    # Apply extra filters
    if property_type:
        properties = properties.filter(property_type=property_type)
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if bedrooms:
        properties = properties.filter(bedrooms__gte=bedrooms)

    if query:
        # Step 1: try location match
        location_filtered = properties.filter(
            Q(location__city__icontains=query)
            | Q(location__state__icontains=query)
            | Q(location__country__icontains=query)
            | Q(location__name__icontains=query)
        )

        # Step 2: semantic re-ranking always applied
        try:
            model = get_model()
            query_embedding = model.encode(query).tolist()

            if location_filtered.exists():
                # Location match found — semantic re-rank within location results
                properties = (
                    location_filtered
                    .filter(embedding__isnull=False)
                    .annotate(similarity=CosineDistance("embedding", query_embedding))
                    .order_by("similarity")
                )
            else:
                # No location match — pure semantic search across all properties
                properties = (
                    properties
                    .filter(embedding__isnull=False)
                    .annotate(similarity=CosineDistance("embedding", query_embedding))
                    .filter(similarity__lte=0.9)
                    .order_by("similarity")
                )
        except Exception:
            # Fallback to location filter only if semantic fails
            if location_filtered.exists():
                properties = location_filtered.order_by("-is_featured", "-created_at")
            else:
                properties = properties.order_by("-is_featured", "-created_at")
    else:
        properties = properties.order_by("-is_featured", "-created_at")

    paginator = Paginator(properties, 9)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "property_app/search_results.html", {
        "page_obj": page_obj,
        "location_query": query,
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


def semantic_search_api(request):
    """JSON API for semantic search."""
    query = request.GET.get("q", "").strip()
    limit = int(request.GET.get("limit", 10))

    if not query:
        return JsonResponse({"error": "Query is required"}, status=400)

    try:
        results = semantic_property_search(query, limit=limit)
        data = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "location": f"{p.location.city}, {p.location.state}",
                "price": str(p.price),
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "property_type": p.property_type,
                "similarity_score": round(float(p.similarity), 4),
            }
            for p in results
        ]
        return JsonResponse({"query": query, "results": data, "count": len(data)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)