"""
Badge definitions and award logic for Gamification & Streaks.

All available badge keys:
  first_entry, streak_3, streak_7, streak_30,
  tasks_10, tasks_50, tasks_100,
  happy_7days, event_creator, sharer
"""
from django.contrib.auth.models import User
from .models import Badge, UserBadge, UserStreak, DiaryEntry, Task, Event, SharePermission

# ---------------------------------------------------------------------------
# Badge catalogue — initialised by the `seed_badges` management command or
# by calling ensure_badges() from a migration data file.
# ---------------------------------------------------------------------------
BADGE_CATALOGUE = [
    {
        'key': 'first_entry',
        'name': 'First Words',
        'description': 'Wrote your very first diary entry.',
        'emoji': '✍️',
    },
    {
        'key': 'streak_3',
        'name': '3-Day Streak',
        'description': 'Journaled for 3 consecutive days.',
        'emoji': '🔥',
    },
    {
        'key': 'streak_7',
        'name': 'Week Warrior',
        'description': 'Journaled for 7 consecutive days.',
        'emoji': '🔥',
    },
    {
        'key': 'streak_30',
        'name': 'Monthly Master',
        'description': 'Journaled for 30 consecutive days.',
        'emoji': '💎',
    },
    {
        'key': 'tasks_10',
        'name': 'Getting Things Done',
        'description': 'Completed 10 tasks.',
        'emoji': '✅',
    },
    {
        'key': 'tasks_50',
        'name': 'Productivity Pro',
        'description': 'Completed 50 tasks.',
        'emoji': '⚡',
    },
    {
        'key': 'tasks_100',
        'name': 'Century Club',
        'description': 'Completed 100 tasks.',
        'emoji': '🏆',
    },
    {
        'key': 'happy_7days',
        'name': 'Happy Streak',
        'description': "Logged 'Happy' mood 7 times.",
        'emoji': '😊',
    },
    {
        'key': 'event_creator',
        'name': 'Planner',
        'description': 'Created your first event.',
        'emoji': '🗓️',
    },
    {
        'key': 'sharer',
        'name': 'Team Player',
        'description': 'Shared content with a colleague.',
        'emoji': '🤝',
    },
]


def ensure_badges():
    """Create any missing Badge records from the catalogue. Safe to call multiple times."""
    for defn in BADGE_CATALOGUE:
        Badge.objects.get_or_create(
            key=defn['key'],
            defaults={
                'name': defn['name'],
                'description': defn['description'],
                'emoji': defn['emoji'],
            }
        )


def _award(user, key):
    """Award badge `key` to `user` if not already earned. Returns True if newly awarded."""
    try:
        badge = Badge.objects.get(key=key)
    except Badge.DoesNotExist:
        return False
    _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    return created


def evaluate_and_award(user):
    """
    Evaluate all badge criteria for `user` and award any newly earned badges.
    Returns a list of newly awarded Badge objects (for toast notifications etc.)
    """
    ensure_badges()
    newly_earned = []

    # --- Streak badges ---
    try:
        streak = user.streak
    except UserStreak.DoesNotExist:
        streak = None

    if streak:
        if streak.current_streak >= 3 and _award(user, 'streak_3'):
            newly_earned.append(Badge.objects.get(key='streak_3'))
        if streak.current_streak >= 7 and _award(user, 'streak_7'):
            newly_earned.append(Badge.objects.get(key='streak_7'))
        if streak.current_streak >= 30 and _award(user, 'streak_30'):
            newly_earned.append(Badge.objects.get(key='streak_30'))

    # --- Diary badges ---
    entry_count = DiaryEntry.objects.filter(user=user).count()
    if entry_count >= 1 and _award(user, 'first_entry'):
        newly_earned.append(Badge.objects.get(key='first_entry'))

    happy_count = DiaryEntry.objects.filter(user=user, mood='happy').count()
    if happy_count >= 7 and _award(user, 'happy_7days'):
        newly_earned.append(Badge.objects.get(key='happy_7days'))

    # --- Task badges ---
    completed_tasks = Task.objects.filter(user=user, completed=True).count()
    if completed_tasks >= 10 and _award(user, 'tasks_10'):
        newly_earned.append(Badge.objects.get(key='tasks_10'))
    if completed_tasks >= 50 and _award(user, 'tasks_50'):
        newly_earned.append(Badge.objects.get(key='tasks_50'))
    if completed_tasks >= 100 and _award(user, 'tasks_100'):
        newly_earned.append(Badge.objects.get(key='tasks_100'))

    # --- Event badges ---
    event_count = Event.objects.filter(user=user).count()
    if event_count >= 1 and _award(user, 'event_creator'):
        newly_earned.append(Badge.objects.get(key='event_creator'))

    # --- Sharing badges ---
    share_count = SharePermission.objects.filter(owner=user).count()
    if share_count >= 1 and _award(user, 'sharer'):
        newly_earned.append(Badge.objects.get(key='sharer'))

    return newly_earned
