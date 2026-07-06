from rest_framework import serializers
from .models import DiaryEntry, Task, Event, Profile, Quote, Reminder
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class DiaryEntrySerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, read_only=True)
    owner_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DiaryEntry
        fields = ['id', 'content', 'mood', 'image', 'tags', 'created_at', 'owner_username']
        read_only_fields = ['id', 'created_at', 'owner_username']

class TaskSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'due_date', 'due_time', 'tags', 'created_at']
        read_only_fields = ['id', 'created_at']

class EventSerializer(serializers.ModelSerializer):
    time = serializers.TimeField(source='event_time', format='%H:%M')
    owner_username = serializers.CharField(source='user.username', read_only=True)
    shared_emails = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'location', 'time', 'date', 'completed', 'attendance_status', 'original_date', 'original_time', 'owner_username', 'shared_emails']
        read_only_fields = ['id', 'owner_username', 'shared_emails']

    def get_shared_emails(self, obj):
        return ", ".join(obj.shares.values_list('shared_with_email', flat=True))


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['id', 'text', 'author']


class ReminderSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='user.username', read_only=True)
    target_title = serializers.SerializerMethodField(read_only=True)
    target_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id', 'diary_entry', 'event', 'task', 'reminder_time', 
            'email_sent', 'created_at', 'owner_username', 
            'target_title', 'target_type'
        ]
        read_only_fields = ['id', 'email_sent', 'created_at', 'owner_username']

    def get_target_title(self, obj):
        if obj.diary_entry:
            return f"Diary Entry on {obj.diary_entry.created_at.strftime('%Y-%m-%d')}"
        elif obj.event:
            return obj.event.title
        elif obj.task:
            return obj.task.title
        return "Unknown"

    def get_target_type(self, obj):
        if obj.diary_entry:
            return "diary"
        elif obj.event:
            return "event"
        elif obj.task:
            return "task"
        return "general"

    def validate(self, data):
        diary_entry = data.get('diary_entry')
        event = data.get('event')
        task = data.get('task')
        
        targets = [diary_entry, event, task]
        if not any(targets):
            raise serializers.ValidationError("A reminder must be associated with a Diary Entry, Event, or Task.")
        if sum(1 for t in targets if t is not None) > 1:
            raise serializers.ValidationError("A reminder can only be associated with one item.")
        return data

