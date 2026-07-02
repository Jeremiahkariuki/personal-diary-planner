from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import log_activity

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Detect the login method
    method = "Standard"
    if hasattr(request, 'sociallogin'):
        provider = request.sociallogin.account.provider
        method = provider.capitalize()
    elif 'google' in request.path or 'social' in request.path:
        method = "Google"

    log_activity(user, 'login', f"Logged in successfully via {method}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_activity(user, 'logout', "Logged out of the system")
