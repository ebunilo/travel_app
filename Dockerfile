# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=alx_travel_app.settings \
    PORT=8000

# System deps for Pillow, psycopg2-binary (or psycopg2), and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# If your requirements file is elsewhere, adjust the path.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static in case you serve docs/static later (safe if not present)
# Uncomment if you have STATIC_ROOT configured.
# RUN python manage.py collectstatic --noinput || true

# Create non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Healthcheck (adjust the URL if needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ || exit 1

# Use Gunicorn to serve the Django app
# Replace 'alx_travel_app.wsgi:application' if your wsgi module differs.
CMD ["gunicorn", "alx_travel_app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
