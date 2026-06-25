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
    image = models.ImageField(upload_to='diary_entries/', null=True, blank=True)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    event_time = models.TimeField()
    date = models.DateField(default=date.today, db_index=True)
    completed = models.BooleanField(default=False, db_index=True)
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
