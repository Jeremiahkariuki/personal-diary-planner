from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.contrib.auth.models import User

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # If the social account is already connected, do nothing
        if sociallogin.is_existing:
            return

        # Check if a user with this email already exists
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                # Link the social account to the existing user
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def is_auto_signup_allowed(self, request, sociallogin):
        # Force auto-signup to skip the signup form
        return True

    def list_apps(self, request, provider=None, client_id=None):
        apps = super().list_apps(request, provider=provider, client_id=client_id)
        deduped = {}
        for app in apps:
            key = (app.provider, app.client_id)
            if key not in deduped:
                deduped[key] = app
            else:
                # Prioritize database-backed apps (they have a primary key/id)
                if getattr(app, 'pk', None) is not None:
                    deduped[key] = app
        return list(deduped.values())
