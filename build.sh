#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Auto-configure the Django Sites domain and SocialApps for OAuth callbacks
python manage.py shell -c "
import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings

# 1. Update Site domain
domain = getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8080')
name = getattr(settings, 'SITE_NAME', 'Jdiary Planner')
site, created = Site.objects.get_or_create(id=settings.SITE_ID)
site.domain = domain
site.name = name
site.save()
print(f'[build] Site domain set to: {domain}')

# 2. Sync Google SocialApp configuration to database
google_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
google_secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
if google_id and google_secret:
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={
            'name': 'Google Login',
            'client_id': google_id,
            'secret': google_secret,
        }
    )
    if not created:
        app.client_id = google_id
        app.secret = google_secret
        app.save()
    app.sites.add(site)
    print('[build] Google SocialApp configured successfully.')
else:
    print('[build] GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found. Skipping Google SocialApp sync.')

# 3. Sync Facebook SocialApp configuration to database
fb_id = os.getenv('FACEBOOK_APP_ID', '').strip()
fb_secret = os.getenv('FACEBOOK_APP_SECRET', '').strip()
if fb_id and fb_secret:
    app, created = SocialApp.objects.get_or_create(
        provider='facebook',
        defaults={
            'name': 'Facebook Login',
            'client_id': fb_id,
            'secret': fb_secret,
        }
    )
    if not created:
        app.client_id = fb_id
        app.secret = fb_secret
        app.save()
    app.sites.add(site)
    print('[build] Facebook SocialApp configured successfully.')
else:
    print('[build] FACEBOOK_APP_ID or FACEBOOK_APP_SECRET not found. Skipping Facebook SocialApp sync.')
"
