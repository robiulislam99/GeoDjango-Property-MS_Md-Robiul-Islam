from django.contrib import admin
from django.utils.html import format_html
from .models import Location, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "image_preview", "alt_text", "is_primary", "sort_order")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:4px;" />',
                obj.image.url,
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "country", "is_active", "created_at")
    list_filter = ("country", "state", "is_active")
    search_fields = ("name", "city", "country")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "location", "property_type", "status",
        "price", "bedrooms", "bathrooms", "is_featured", "is_active",
    )
    list_filter = ("property_type", "status", "is_featured", "is_active", "location__country")
    search_fields = ("title", "address", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [PropertyImageInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "image_preview", "is_primary", "sort_order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("property__title", "alt_text")
    readonly_fields = ("image_preview", "created_at")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:80px; border-radius:4px;" />',
                obj.image.url,
            )
        return "No image"
    image_preview.short_description = "Preview"