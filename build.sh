#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Auto-configure the Django Sites domain for OAuth callbacks
# Uses RENDER_EXTERNAL_HOSTNAME if available, otherwise SITE_DOMAIN env var
python manage.py shell -c "
from django.contrib.sites.models import Site
from django.conf import settings
domain = getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8000')
name = getattr(settings, 'SITE_NAME', 'Jdiary Planner')
site = Site.objects.get_or_create(id=settings.SITE_ID)[0]
site.domain = domain
site.name = name
site.save()
print(f'[build] Site domain set to: {domain}')
"
