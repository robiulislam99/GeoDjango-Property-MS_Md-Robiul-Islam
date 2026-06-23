from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance
from property_app.models import Property, Location


TEST_QUERIES = [
    "luxury beach house with pool",
    "cozy mountain cabin with fireplace",
    "cheap city apartment for couples",
    "family friendly cottage near lake",
    "desert hideaway with stargazing",
    "modern loft in downtown manhattan",
]


class Command(BaseCommand):
    help = "Test semantic search with sample queries"

    def handle(self, *args, **options):
        self.stdout.write("Loading model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        self.stdout.write(self.style.SUCCESS("Model loaded!\n"))

        for query in TEST_QUERIES:
            self.stdout.write(f"Query: '{query}'")
            embedding = model.encode(query).tolist()

            results = (
                Property.objects.filter(is_active=True, embedding__isnull=False)
                .annotate(similarity=CosineDistance("embedding", embedding))
                .order_by("similarity")[:3]
            )

            for i, prop in enumerate(results, 1):
                self.stdout.write(
                    f"  {i}. {prop.title} "
                    f"({prop.location.city}) "
                    f"— score: {prop.similarity:.4f}"
                )
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Testing complete!"))