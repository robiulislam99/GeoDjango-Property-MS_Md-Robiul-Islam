from django.contrib.gis.db import models
from pgvector.django import VectorField, HnswIndex


class Location(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    point = models.PointField(geography=True, srid=4326, null=True, blank=True)
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}, {self.city}, {self.country}"

    class Meta:
        indexes = [
            HnswIndex(
                name="location_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")

    def __str__(self):
        return self.name

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ("house", "House"),
        ("apartment", "Apartment"),
        ("villa", "Villa"),
        ("cabin", "Cabin"),
        ("condo", "Condo"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("available", "Available"),
        ("booked", "Booked"),
        ("inactive", "Inactive"),
    ]

    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="properties"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="available")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    area_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True)
    point = models.PointField(geography=True, srid=4326, null=True, blank=True)
    footprint = models.PolygonField(srid=4326, null=True, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Properties"
        indexes = [
            HnswIndex(
                name="property_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="properties/%Y/%m/")
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.property.title} (#{self.pk})"

    class Meta:
        ordering = ["sort_order", "id"]


