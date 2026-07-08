from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class DiaryEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('neutral', '😐 Neutral'),
        ('sad', '😔 Sad'),
        ('excited', '🤩 Excited'),
        ('stressed', '😫 Stressed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    content = models.TextField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='neutral')
    image = models.ImageField(upload_to='diary/%Y/%m/', null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='diary_entries')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Entry by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')} ({self.mood})"

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False, db_index=True)
    due_date = models.DateField(blank=True, null=True, db_index=True)
    due_time = models.TimeField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['completed', 'due_date', 'due_time', '-created_at']

    def __str__(self):
        return self.title

class Event(models.Model):
    ATTENDANCE_CHOICES = [
        ('pending', 'Pending'),
        ('attended', 'Attended'),
        ('unattended', 'Unattended'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    event_time = models.TimeField()
    date = models.DateField(default=date.today, db_index=True)
    completed = models.BooleanField(default=False, db_index=True)
    notified = models.BooleanField(default=False)
    attendance_status = models.CharField(max_length=12, choices=ATTENDANCE_CHOICES, default='pending', db_index=True)
    original_date = models.DateField(null=True, blank=True)
    original_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'event_time']

    def __str__(self):
        return f"{self.title} at {self.event_time}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    custom_quote = models.TextField(blank=True, null=True)
    custom_quote_author = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Quote(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.text[:50]


class SystemActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login',           '🔐 Login'),
        ('logout',          '🚪 Logout'),
        ('dashboard_view',  '📊 Dashboard Viewed'),
        ('diary_write',     '✍️ Diary Written'),
        ('diary_edit',      '📝 Diary Edited'),
        ('diary_view',      '📖 Diary Viewed'),
        ('diary_delete',    '🗑️ Diary Deleted'),
        ('task_view',       '✅ Tasks Viewed'),
        ('task_create',     '➕ Task Created'),
        ('task_edit',       '✏️ Task Updated'),
        ('task_complete',   '🎯 Task Completed'),
        ('task_delete',     '🗑️ Task Deleted'),
        ('event_view',      '📅 Events Viewed'),
        ('event_create',    '🗓️ Event Created'),
        ('event_edit',      '✏️ Event Updated'),
        ('event_delete',    '🗑️ Event Deleted'),
        ('profile_view',    '👤 Profile Viewed'),
        ('settings_view',   '⚙️ Settings Visited'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.CharField(max_length=300)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.user.username}] {self.action} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def get_action_label(self):
        return dict(self.ACTION_CHOICES).get(self.action, self.action)


def log_activity(user, action, description):
    """Create a SystemActivityLog entry; silently ignore errors."""
    try:
        SystemActivityLog.objects.create(user=user, action=action, description=description)
    except Exception:
        pass


class SharePermission(models.Model):
    SHARE_TYPE_CHOICES = [
        ('specific_diary', 'Specific Diary Entry'),
        ('whole_diary', 'Whole Diary'),
        ('specific_event', 'Specific Event'),
        ('whole_events', 'Whole Events'),
        ('whole_tasks', 'Whole Tasks'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_granted')
    shared_with_email = models.EmailField(db_index=True)
    shared_with_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shares_received')
    share_type = models.CharField(max_length=20, choices=SHARE_TYPE_CHOICES)
    diary_entry = models.ForeignKey(DiaryEntry, on_delete=models.CASCADE, null=True, blank=True, related_name='shares')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='shares')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('owner', 'shared_with_email', 'share_type', 'diary_entry', 'event')

    def __str__(self):
        target = ""
        if self.share_type == 'specific_diary':
            target = f"Diary Entry {self.diary_entry_id}"
        elif self.share_type == 'specific_event':
            target = f"Event '{self.event.title}'"
        else:
            target = self.get_share_type_display()
        return f"{self.owner.email} shared {target} with {self.shared_with_email}"


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    diary_entry = models.ForeignKey(DiaryEntry, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    reminder_time = models.DateTimeField(db_index=True)
    email_sent = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_time']

    def clean(self):
        from django.core.exceptions import ValidationError
        targets = [self.diary_entry, self.event, self.task]
        if not any(targets):
            raise ValidationError("A reminder must be associated with a Diary Entry, Event, or Task.")
        if sum(1 for t in targets if t is not None) > 1:
            raise ValidationError("A reminder can only be associated with one item (Diary Entry, Event, or Task).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        target = ""
        if self.diary_entry:
            target = f"Diary Entry #{self.diary_entry.id}"
        elif self.event:
            target = f"Event '{self.event.title}'"
        elif self.task:
            target = f"Task '{self.task.title}'"
        return f"Reminder for {self.user.username} - {target} at {self.reminder_time.strftime('%Y-%m-%d %H:%M')}"



