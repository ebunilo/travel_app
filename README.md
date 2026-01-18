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
- PostgreSQL
- Pillow (images)
- Celery + Redis (optional for email notifications)

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
- Redis (optional, for Celery tasks)
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
Create a `.env` file in the project root with the following variables:
    ```env
    DEBUG=True
    SECRET_KEY=your_secret_key
    DATABASE_URL=postgres://user:password@localhost:5432/alx_travel_app
    CHAPA_API_KEY=your_chapa_api_key
    ALLOWED_HOSTS=localhost,
    CORS_ALLOWED_ORIGINS=http://localhost:3000
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

## Testing Payment Integration
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
