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
