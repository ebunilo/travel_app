#!/bin/bash
set -e

# Run migrations and collect static files as root (before switching user)
echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Ensure the staticfiles and media directories have proper permissions
echo "Fixing permissions..."
chmod -R 755 /app/staticfiles
chmod -R 755 /app/media

# Start the application
echo "Starting Gunicorn..."
exec gunicorn alx_travel_app.wsgi:application --bind 0.0.0.0:8000 --workers 3
