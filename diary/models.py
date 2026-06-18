from django.db import models
from django.contrib.auth.models import User
from datetime import date

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Entry by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')} ({self.mood})"

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'due_date', 'due_time', '-created_at']

    def __str__(self):
        return self.title

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    event_time = models.TimeField()
    date = models.DateField(default=date.today)
    completed = models.BooleanField(default=False)
    notified = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'event_time']

    def __str__(self):
        return f"{self.title} at {self.event_time}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"

class Quote(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.text[:50]
