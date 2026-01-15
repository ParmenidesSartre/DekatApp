#!/usr/bin/env bash
# Startup script for Render - runs migrations then starts gunicorn

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
