import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils.text import slugify
from django.core.files.base import ContentFile
from property_app.models import Location, Property, Amenity, PropertyImage


class Command(BaseCommand):
    help = "Import properties from CSV including image download"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        df = pd.read_csv(csv_path)

        self.stdout.write(f"Found {len(df)} rows. Importing...")

        created_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            # Get or create Location
            location, _ = Location.objects.get_or_create(
                city=row["city"],
                country=row["country"],
                defaults={
                    "name": f"{row['city']}, {row['state']}",
                    "slug": slugify(f"{row['city']}-{row['state']}-{row['country']}"),
                    "state": row.get("state", ""),
                    "point": Point(
                        float(row["longitude"]),
                        float(row["latitude"]),
                        srid=4326
                    ),
                },
            )

            # Build unique slug
            base_slug = slugify(row["title"])
            slug = base_slug
            counter = 1
            while Property.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create Property
            prop, created = Property.objects.get_or_create(
                title=row["title"],
                defaults={
                    "slug": slug,
                    "location": location,
                    "description": row.get("description", ""),
                    "property_type": row.get("property_type", "other"),
                    "status": row.get("status", "available"),
                    "price": row["price"],
                    "bedrooms": int(row.get("bedrooms", 0)),
                    "bathrooms": int(row.get("bathrooms", 0)),
                    "area_sqft": row.get("area_sqft") or None,
                    "address": row.get("address", ""),
                    "point": Point(
                        float(row.get("prop_longitude", row["longitude"])),
                        float(row.get("prop_latitude", row["latitude"])),
                        srid=4326
                    ),
                },
            )

            if created:
                # Handle amenities
                amenities_raw = row.get("amenities", "")
                if pd.notna(amenities_raw) and amenities_raw:
                    for amenity_str in str(amenities_raw).split("|"):
                        amenity_str = amenity_str.strip()
                        if not amenity_str:
                            continue
                        parts = amenity_str.split(" ", 1)
                        icon, name = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
                        amenity, _ = Amenity.objects.get_or_create(
                            name=name,
                            defaults={"icon": icon}
                        )
                        prop.amenities.add(amenity)

                # Handle images
                image_urls_raw = row.get("image_urls", "")
                if pd.notna(image_urls_raw) and image_urls_raw:
                    urls = str(image_urls_raw).split("|")
                    for i, url in enumerate(urls):
                        url = url.strip()
                        if not url:
                            continue
                        try:
                            self.stdout.write(f"    Downloading image {i+1} for {prop.title}...")
                            response = requests.get(url, timeout=15)
                            response.raise_for_status()
                            filename = f"{prop.slug}-{i+1}.jpg"
                            image = PropertyImage(
                                property=prop,
                                is_primary=(i == 0),
                                sort_order=i,
                                alt_text=prop.title,
                            )
                            image.image.save(
                                filename,
                                ContentFile(response.content),
                                save=True
                            )
                            self.stdout.write(self.style.SUCCESS(f"    ✔ Image saved: {filename}"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"    ⚠ Image failed: {e}"))

                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✔ Created: {prop.title}"))
            else:
                skipped_count += 1
                self.stdout.write(f"  — Skipped (exists): {prop.title}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created: {created_count}, Skipped: {skipped_count}"
        ))