#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create media directories
mkdir -p media/qr_codes

# Create superuser if environment variables are set
if [[ $DJANGO_SUPERUSER_USERNAME ]]; then
  python manage.py createsuperuser --no-input || true
fi
