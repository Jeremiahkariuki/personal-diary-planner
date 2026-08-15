from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import log_activity, SharePermission, DiaryEntry, UserStreak

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


@receiver(post_save, sender=DiaryEntry)
def on_diary_entry_saved(sender, instance, created, **kwargs):
    """Update the user's journaling streak and evaluate badges on every diary entry save."""
    if not created:
        return  # Only care about new entries for streak calculation

    user = instance.user
    entry_date = instance.created_at.date()

    # Update streak
    streak, _ = UserStreak.objects.get_or_create(user=user)
    streak.update(entry_date)

    # Evaluate and award badges (import here to avoid circular imports)
    try:
        from .badges import evaluate_and_award
        evaluate_and_award(user)
    except Exception:
        pass  # Never break diary writes due to badge errors
