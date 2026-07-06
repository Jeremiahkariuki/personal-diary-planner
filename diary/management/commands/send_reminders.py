"""
Management command: send_reminders
Runs in a loop, checking every 60 seconds for due reminders and emailing users.

Usage:
    python manage.py send_reminders           # loop forever (default)
    python manage.py send_reminders --once    # run once and exit (for cron jobs)
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send reminder emails for due reminders. Runs in a loop by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single check instead of looping forever.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Seconds between checks when running in loop mode (default: 60).",
        )

    def handle(self, *args, **options):
        once = options["once"]
        interval = options["interval"]

        if once:
            self.stdout.write(self.style.SUCCESS("[send_reminders] Running one-time check…"))
            count = self._process_due_reminders()
            self.stdout.write(self.style.SUCCESS(f"[send_reminders] Done. Sent {count} email(s)."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[send_reminders] Starting reminder daemon — checking every {interval}s. Press Ctrl+C to stop."
                )
            )
            while True:
                try:
                    count = self._process_due_reminders()
                    if count:
                        self.stdout.write(self.style.SUCCESS(f"[send_reminders] Sent {count} reminder email(s)."))
                except Exception as exc:
                    self.stderr.write(f"[send_reminders] ERROR: {exc}")
                    logger.exception("Unexpected error in send_reminders loop")
                time.sleep(interval)

    def _process_due_reminders(self):
        """Find all unsent, due reminders and email the users. Returns number sent."""
        from diary.models import Reminder  # local import avoids circular imports at startup

        now = timezone.now()
        due = Reminder.objects.filter(reminder_time__lte=now, email_sent=False).select_related(
            "user", "event", "task", "diary_entry"
        )

        sent = 0
        for reminder in due:
            try:
                subject, body = self._build_email(reminder)
                recipient = reminder.user.email
                if not recipient:
                    self.stderr.write(
                        f"[send_reminders] User {reminder.user.username} has no email — skipping reminder #{reminder.id}"
                    )
                    continue

                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                    fail_silently=False,
                )
                reminder.email_sent = True
                reminder.save(update_fields=["email_sent"])
                sent += 1
                self.stdout.write(
                    f"[send_reminders] Sent reminder email to {recipient} — {subject}"
                )
            except Exception as exc:
                self.stderr.write(
                    f"[send_reminders] Failed to send reminder #{reminder.id}: {exc}"
                )
                logger.exception("Failed to send reminder #%s", reminder.id)

        return sent

    def _build_email(self, reminder):
        """Return (subject, body) for a given Reminder instance."""
        user = reminder.user
        name = user.get_full_name() or user.username

        if reminder.event:
            item = reminder.event
            subject = f"🔔 Reminder: Event — {item.title}"
            body = (
                f"Hi {name},\n\n"
                f"This is your scheduled reminder for the following event:\n\n"
                f"  📅 Event : {item.title}\n"
                f"  📍 Location : {item.location or 'Not specified'}\n"
                f"  🕒 Date & Time : {item.date} at {item.event_time.strftime('%H:%M')}\n\n"
                f"Log in to JDiary to view more details.\n\n"
                f"— The JDiary Team"
            )

        elif reminder.task:
            item = reminder.task
            status = "✅ Completed" if item.completed else "⏳ Pending"
            due_str = f"{item.due_date}" if item.due_date else "No due date set"
            subject = f"🔔 Reminder: Task — {item.title}"
            body = (
                f"Hi {name},\n\n"
                f"This is your scheduled reminder for the following task:\n\n"
                f"  📝 Task   : {item.title}\n"
                f"  📋 Status : {status}\n"
                f"  📅 Due    : {due_str}\n"
                + (f"  📄 Notes  : {item.description}\n" if item.description else "")
                + f"\nLog in to JDiary to manage your tasks.\n\n"
                f"— The JDiary Team"
            )

        elif reminder.diary_entry:
            item = reminder.diary_entry
            mood_map = {
                "happy": "😊 Happy", "excited": "🤩 Excited", "neutral": "😐 Neutral",
                "sad": "😔 Sad", "stressed": "😫 Stressed"
            }
            mood_label = mood_map.get(item.mood, item.mood.capitalize())
            snippet = item.content[:200] + ("…" if len(item.content) > 200 else "")
            subject = f"🔔 Reminder: Diary Entry from {item.created_at.strftime('%b %d, %Y')}"
            body = (
                f"Hi {name},\n\n"
                f"This is your scheduled reminder for a diary entry:\n\n"
                f"  📅 Written : {item.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"  😊 Mood    : {mood_label}\n"
                f"  📖 Preview : {snippet}\n\n"
                f"Log in to JDiary to read the full entry.\n\n"
                f"— The JDiary Team"
            )

        else:
            subject = "🔔 JDiary Reminder"
            body = (
                f"Hi {name},\n\n"
                f"You have a scheduled reminder. Log in to JDiary to see your items.\n\n"
                f"— The JDiary Team"
            )

        return subject, body
