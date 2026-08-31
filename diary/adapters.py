# pyrefly: ignore [missing-import]
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

    def get_app(self, request, provider, client_id=None):
        apps = self.list_apps(request, provider=provider, client_id=client_id)
        if not apps:
            from allauth.socialaccount.models import SocialApp
            app, _ = SocialApp.objects.get_or_create(
                provider=provider,
                defaults={'name': provider.capitalize(), 'client_id': 'placeholder', 'secret': 'placeholder'}
            )
            return app
        return apps[0]

