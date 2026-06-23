from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance
from .models import Property, Location

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def semantic_property_search(query_text, limit=10, threshold=0.9):
    """
    Higher threshold = more results returned.
    0.9 is very permissive — catches even weak matches.
    """
    model = get_model()
    query_embedding = model.encode(query_text).tolist()

    results = (
        Property.objects.filter(is_active=True, embedding__isnull=False)
        .annotate(similarity=CosineDistance("embedding", query_embedding))
        .filter(similarity__lte=threshold)
        .order_by("similarity")
        .select_related("location")
        .prefetch_related("images", "amenities")[:limit]
    )
    return results


def semantic_location_search(query_text, limit=5):
    model = get_model()
    query_embedding = model.encode(query_text).tolist()

    results = (
        Location.objects.filter(is_active=True, embedding__isnull=False)
        .annotate(similarity=CosineDistance("embedding", query_embedding))
        .order_by("similarity")[:limit]
    )
    return results