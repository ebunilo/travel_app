# ALX Travel App

A Django + Django REST Framework application for managing property listings, bookings, reviews, and payments via Chapa.

## Features

- Listings CRUD via REST API
- Booking creation with automatic price calculation
- Reviews with unique-per-user-per-listing constraint
- Payment initiation and verification with Chapa
- Swagger UI for API docs

## Tech Stack

- Django 5.2.9
- Django REST Framework
- drf-yasg (Swagger)
- django-environ
- django-cors-headers
- PostgreSQL (psycopg)
- Pillow (images)
- Celery + Redis (async tasks and broker)

## Project Structure

- Core settings: [alx_travel_app/settings.py](alx_travel_app/settings.py)
- URLs: [alx_travel_app/urls.py](alx_travel_app/urls.py)
- Listings app:
  - Models: [listings/models.py](listings/models.py)
  - Views: [listings/views.py](listings/views.py)
  - Serializers: [listings/serializers.py](listings/serializers.py)
  - API routes: [listings/urls.py](listings/urls.py)
  - Admin: [listings/admin.py](listings/admin.py)
  - Seed command: [listings/management/commands/seed.py](listings/management/commands/seed.py)
  - Migrations: [listings/migrations](listings/migrations)

Key symbols:

- [`listings.models.Listing`](listings/models.py)
- [`listings.models.Booking`](listings/models.py)
- [`listings.models.Review`](listings/models.py)
- [`listings.models.Payment`](listings/models.py)
- [`listings.views.ListingViewSet`](listings/views.py)
- [`listings.views.BookingViewSet`](listings/views.py)
- [`listings.views.InitiatePaymentView`](listings/views.py)
- [`listings.views.VerifyPaymentView`](listings/views.py)
- [`listings.serializers.ListingSerializer`](listings/serializers.py)
- [`listings.serializers.BookingSerializer`](listings/serializers.py)

## Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (required if using Celery)
- Docker & Docker Compose (optional, recommended for local containerized dev)
- Virtualenv recommended

## Setup

1. Create and activate a virtual environment.

   ```sh
   # ...existing code...
   python -m venv .venv
   source .venv/bin/activate
   # ...existing code...
   ```

2. Install dependencies.

   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables.
   Create a `.env` file in the project root with the following variables (these match `alx_travel_app/settings.py`):

```env
# Core
DEBUG=True
DJANGO_SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost

# Database (used by settings)
DB_NAME=travel_db
DB_USER=travel_user
DB_PASSWORD=travel_pass
DB_HOST=localhost
DB_PORT=5432

# Payment (Chapa)
CHAPA_SECRET_KEY=your_chapa_secret_key

# Celery / Redis (optional)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@alxtravelapp.com
```

4. Apply migrations.

   ```sh
   python manage.py migrate
   ```

5. (Optional) Seed the database with sample data.

   ```sh
   python manage.py seed
   ```

6. Run the development server.

```sh
python manage.py runserver
```

7. Access the API documentation at `http://localhost:8000/swagger/`.

## API Endpoints (high level)

- Listings: `/api/listings/` (GET/POST) and `/api/listings/{id}/` (GET/PUT/PATCH/DELETE)
- Bookings: `/api/bookings/` and `/api/bookings/{id}/`
- Users: `/api/users/` and `/api/users/{id}/` — full CRUD (list, retrieve, create, update, partial_update, delete). These endpoints are documented in the Swagger UI.

## Celery / Redis (local / Docker)

If you use Docker Compose (recommended), the project includes services for `web`, `db`, `redis`, and `celery` in `docker-compose.yaml`. Redis data is persisted using the `redis_data` volume.

To start services with Docker Compose:

```sh
docker-compose up --build web db redis celery
```

Run only the Celery worker (local / non-Docker):

```sh
# activate virtualenv
celery -A alx_travel_app worker -l info
```

Redis persistence: the Redis service mounts a volume named `redis_data` at `/data` so AOF/RDB data is persisted across restarts.

## Testing Payment Integration

To test the payment integration with Chapa, follow these steps:

1. Use Postman or similar tool to initiate a payment via the `/api/payments/initiate/` endpoint.
2. Complete the payment on Chapa's hosted payment page.
3. Verify the payment status via the `/api/payments/verify/` endpoint.

### Initiate Payment via Postman

![Initiate Payment](images/initiate_payment.png)

### Make Payment via Chapa

![Chapa Payment UI](images/make_payment.png)

### Successful Payment UI

![Successful Payment UI](images/successful_payment.png)

### Verify Payment via Chapa

![Verify Payment](images/verify_payment.png)
