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

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user and set proper permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Create directories that will be used for volumes
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media

# Run entrypoint as root (migrations and collectstatic need to run with permissions)
# But the actual gunicorn process will run as appuser via exec
USER root

EXPOSE 8000

# Healthcheck (adjust the URL if needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
