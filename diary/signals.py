from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import log_activity, SharePermission

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


@receiver(post_save, sender=User)
def link_pending_shares(sender, instance, created, **kwargs):
    if created and instance.email:
        SharePermission.objects.filter(shared_with_email=instance.email).update(shared_with_user=instance)

