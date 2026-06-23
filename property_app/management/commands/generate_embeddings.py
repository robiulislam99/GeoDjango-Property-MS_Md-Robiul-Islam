from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer
from property_app.models import Property, Location

MODEL_NAME = "all-MiniLM-L6-v2"


def build_property_text(prop):
    """Build a rich text representation of a property for embedding."""
    parts = [
        prop.title,
        prop.description,
        f"{prop.bedrooms} bedrooms, {prop.bathrooms} bathrooms",
        f"Property type: {prop.get_property_type_display()}",
        f"Price: ${prop.price} per night",
        f"Location: {prop.location.city}, {prop.location.state}, {prop.location.country}",
    ]
    amenities = prop.amenities.values_list("name", flat=True)
    if amenities:
        parts.append(f"Amenities: {', '.join(amenities)}")
    return " | ".join(filter(None, parts))


def build_location_text(loc):
    """Build a text representation of a location for embedding."""
    parts = [
        loc.name,
        loc.city,
        loc.state,
        loc.country,
        loc.address,
    ]
    return " | ".join(filter(None, parts))


class Command(BaseCommand):
    help = "Generate embeddings for all properties and locations using Sentence Transformers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default=MODEL_NAME,
            help="Sentence transformer model name",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-generate embeddings even if they already exist",
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        force = options["force"]

        self.stdout.write(f"Loading model: {model_name}...")
        model = SentenceTransformer(model_name)
        self.stdout.write(self.style.SUCCESS("Model loaded!"))

        # Generate Property embeddings
        self.stdout.write("\nGenerating property embeddings...")
        properties = Property.objects.prefetch_related("amenities", "location")
        if not force:
            properties = properties.filter(embedding__isnull=True)

        props_list = list(properties)
        if not props_list:
            self.stdout.write("  No properties need embedding (use --force to regenerate)")
        else:
            texts = [build_property_text(p) for p in props_list]
            embeddings = model.encode(texts, show_progress_bar=True)

            for prop, embedding in zip(props_list, embeddings):
                prop.embedding = embedding.tolist()
                prop.save(update_fields=["embedding"])
                self.stdout.write(self.style.SUCCESS(f"  ✔ {prop.title}"))

        # Generate Location embeddings
        self.stdout.write("\nGenerating location embeddings...")
        locations = Location.objects.all()
        if not force:
            locations = locations.filter(embedding__isnull=True)

        locs_list = list(locations)
        if not locs_list:
            self.stdout.write("  No locations need embedding (use --force to regenerate)")
        else:
            loc_texts = [build_location_text(l) for l in locs_list]
            loc_embeddings = model.encode(loc_texts, show_progress_bar=True)

            for loc, embedding in zip(locs_list, loc_embeddings):
                loc.embedding = embedding.tolist()
                loc.save(update_fields=["embedding"])
                self.stdout.write(self.style.SUCCESS(f"  ✔ {loc.name}"))

        self.stdout.write(self.style.SUCCESS("\nAll embeddings generated successfully!"))