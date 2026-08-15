import random
from diary.models import Profile, Quote, UserStreak, UserBadge

def quote_context(request):
    if not request.user.is_authenticated:
        return {}
    
    # Ensuring profile exists
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if profile.custom_quote:
        quote_text = profile.custom_quote
        quote_author = profile.custom_quote_author or ''
        quote_is_custom = True
    else:
        all_quotes = list(Quote.objects.all())
        if all_quotes:
            q = random.choice(all_quotes)
            quote_text = q.text
            quote_author = q.author or ''
        else:
            quote_text = "Every day is a new beginning."
            quote_author = ''
        quote_is_custom = False

    # Streak
    try:
        user_streak = request.user.streak
    except UserStreak.DoesNotExist:
        user_streak = None

    # Recently earned badges (last 3)
    recent_badges = list(UserBadge.objects.filter(user=request.user).select_related('badge')[:3])

    return {
        'quote_text': quote_text,
        'quote_author': quote_author,
        'quote_is_custom': quote_is_custom,
        'profile': profile,
        'user_streak': user_streak,
        'recent_badges': recent_badges,
    }
