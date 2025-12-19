#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Convert static files
python manage.py collectstatic --no-input

# Apply DB migrations
python manage.py migrate

# --- AUTO-CREATE SUPERUSER (Free Tier Hack) ---
# This runs a Python script to create 'admin' if it doesn't exist yet.
# It uses environment variables we will set in Render Dashboard.
echo "Creating superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', '$SUPERUSER_PASSWORD')"