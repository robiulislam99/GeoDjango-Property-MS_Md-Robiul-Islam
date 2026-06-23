# GeoDjango Property Management System

A scalable vacation rental platform built with Django, GeoDjango, PostGIS, and pgvector for spatial and semantic search capabilities.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, GeoDjango, Django REST Framework |
| Frontend | HTML5, CSS3 (Responsive), Vanilla JavaScript |
| Database | PostgreSQL 17 + PostGIS 3 + pgvector |
| AI Search | Sentence Transformers (all-MiniLM-L6-v2) |
| Infrastructure | Docker, Docker Compose |
| Storage | Local media storage (bind mount) |

---

## Project Structure
```
geodjango-property/
├── Dockerfile.postgres          # PostgreSQL + PostGIS + pgvector
├── Dockerfile.django            # Django app + GDAL
├── docker-compose.yml           # Multi-service setup
├── init.sql                     # PostgreSQL extensions
├── requirements.txt
├── manage.py
├── .env
│
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── property_app/
│   ├── models.py                # Location, Property, PropertyImage, Amenity
│   ├── views.py                 # All views
│   ├── urls.py                  # URL routing
│   ├── admin.py                 # Django Admin config
│   ├── semantic_search.py       # pgvector semantic search logic
│   ├── migrations/
│   └── management/
│       └── commands/
│           ├── import_properties.py     # CSV import with Pandas
│           ├── generate_embeddings.py   # Sentence Transformer embeddings
│           └── test_semantic_search.py  # Semantic search testing
│
├── templates/
│   ├── base.html
│   └── property_app/
│       ├── home.html
│       ├── search_results.html
│       ├── property_detail.html
│       └── semantic_search.html
│
├── static/
│   └── css/
│       └── style.css
│
└── data/
└── properties.csv
```
---

## Features

### Location Management
- Country, state, city hierarchy
- Geographic coordinates (PointField)
- Administrative boundaries (MultiPolygonField)
- Spatial indexing via PostGIS
- Semantic search support via pgvector

### Property Management
- Full property listings with geo-coordinates
- Polygon property footprints
- Geo-based distance calculations
- AI-powered semantic search
- Pricing and metadata management
- Amenities with icons

### Search
- Location-based search with filters
- Property type, price range, bedroom filters
- AI semantic search (natural language)
- Combined location + semantic re-ranking
- Pagination

### GIS Features
- Distance from city center calculation
- Radius-based property search
- Nearest property lookup

### AI Features
- Property semantic search
- Location semantic search
- HNSW vector indexing for fast similarity search
- Cosine distance ranking

---

## Prerequisites

- Docker
- Docker Compose
- Git

> No local Python, PostgreSQL, or GDAL installation needed — everything runs in Docker.

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/robiulislam99/GeoDjango-Property-MS_Md-Robiul-Islam.git geodjango-property
cd geodjango-property
```

### 2. Create `.env` file
```env
DB_NAME=appdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
```

### 3. Create media directory
```bash
mkdir -p media
```
> This is where property images will be downloaded during import.

### 4. Build and start containers
> ⚠️ First build takes 5-10 minutes — installs GDAL, CPU-only PyTorch, and all dependencies.
```bash
docker-compose up --build -d
```

### 5. Run migrations
```bash
docker exec -it django-app python manage.py migrate
```

### 6. Create superuser
```bash
docker exec -it django-app python manage.py createsuperuser
```

### 7. Import sample data
> Downloads 40 images from Unsplash automatically. Takes 2-3 minutes.
```bash
docker exec -it django-app python manage.py import_properties data/properties.csv
```

### 8. Generate AI embeddings
> Downloads sentence-transformer model (~90MB) on first run. Subsequent runs are instant.
```bash
docker exec -it django-app python manage.py generate_embeddings
```

### 9. Access the application

| URL | Description |
|---|---|
| http://localhost:8000 | Homepage |
| http://localhost:8000/properties/ | All properties |
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/api/search/semantic/?q=beach+villa | Semantic Search API |
| http://localhost:8000/api/locations/autocomplete/?q=dhaka | Autocomplete API |

> ℹ️ After step 7, all 40 property images will be visible in `./media/` on your machine.
> Semantic AI search is integrated into the main search bar — no separate page needed.
---

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose stop

# View logs
docker logs django-app --tail=30
docker logs postgres-postgis-pgvector --tail=30

# Restart Django only
docker-compose stop django
docker-compose start django

# Rebuild after code changes
docker-compose up --build -d

# Access Django shell
docker exec -it django-app python manage.py shell

# Access PostgreSQL
docker exec -it postgres-postgis-pgvector psql -U postgres -d appdb
```

---

## Management Commands

```bash
# Import properties from CSV
docker exec -it django-app python manage.py import_properties data/properties.csv

# Generate embeddings for all properties and locations
docker exec -it django-app python manage.py generate_embeddings

# Force re-generate all embeddings
docker exec -it django-app python manage.py generate_embeddings --force

# Test semantic search with sample queries
docker exec -it django-app python manage.py test_semantic_search
```

---

## Models

### Location
name, slug, country, state, city, address

point (PointField), boundary (MultiPolygonField)

embedding (VectorField 1536-dim)

### Property
title, slug, description, property_type, status

price, bedrooms, bathrooms, area_sqft, address

point (PointField), footprint (PolygonField)

embedding (VectorField 1536-dim)

location (FK), amenities (M2M)

### PropertyImage
image, alt_text, caption, width, height, file_size

embedding (VectorField 768-dim)

is_primary, sort_order

property (FK)

### Amenity
name, icon

---

## API Endpoints

### Location Autocomplete
GET /api/locations/autocomplete/?q=destin
```json
{
  "results": [
    {"id": 1, "label": "Destin, Florida, USA", "slug": "destin-florida-usa"}
  ]
}
```

### Semantic Search
GET /api/search/semantic/?q=luxury+beach+villa+with+pool&limit=5
```json
{
  "query": "luxury beach villa with pool",
  "count": 3,
  "results": [
    {
      "id": 1,
      "title": "King's Castle Beach House",
      "slug": "kings-castle-beach-house",
      "location": "Destin, Florida",
      "price": "450.00",
      "bedrooms": 6,
      "bathrooms": 4,
      "property_type": "villa",
      "similarity_score": 0.1823
    }
  ]
}
```

---

## Spatial Queries (Examples)

```python
# Properties within 5km of a point
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point

Property.objects.filter(
    point__distance_lte=(Point(90.4125, 23.8103), D(km=5))
)

# Properties ordered by distance from a point
from django.contrib.gis.db.models.functions import Distance

Property.objects.annotate(
    distance=Distance("point", Point(90.4125, 23.8103))
).order_by("distance")
```

## Vector Queries (Examples)

```python
# Semantic search with cosine distance
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode("luxury beach villa").tolist()

Property.objects.annotate(
    similarity=CosineDistance("embedding", embedding)
).order_by("similarity")[:10]
```

---

## HNSW Index

Vector fields use HNSW indexing for fast approximate nearest neighbor search:

```python
HnswIndex(
    name="property_embedding_idx",
    fields=["embedding"],
    m=16,
    ef_construction=64,
    opclasses=["vector_cosine_ops"]
)
```

Verify indexes:
```bash
docker exec -it postgres-postgis-pgvector psql -U postgres -d appdb -c "
SELECT indexname FROM pg_indexes WHERE indexname LIKE '%embedding%';
"
```

---

## Development Notes

- `DEBUG=True` — do not use in production
- Static files served by Django dev server via `django.contrib.staticfiles`
- Media files stored in `./media/` on host machine (bind mount to `/app/media/` in container)
- Sentence Transformer model is preloaded at Django startup via `apps.py` ready() method
- Embeddings dimension: **384** (all-MiniLM-L6-v2 actual output) — both Property and Location fields use 384
- PyTorch installed as **CPU-only** via dedicated wheel — reduces Docker image size from ~2GB to ~200MB
- Images are **not committed to git** — run `import_properties` to download them automatically
- `torch` is excluded from `requirements.txt` — installed separately in `Dockerfile.django` before other dependencies

---


## References

- [GeoDjango](https://docs.djangoproject.com/en/5.0/ref/contrib/gis/)
- [PostGIS](https://postgis.net/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Sentence Transformers](https://www.sbert.net/)
- [pgvector-python](https://github.com/pgvector/pgvector-python)
