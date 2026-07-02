from rest_framework import serializers
from .models import DiaryEntry, Task, Event, Profile, Quote
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
        fields = ['id', 'title', 'location', 'time', 'date', 'completed', 'owner_username', 'shared_emails']
        read_only_fields = ['id', 'owner_username', 'shared_emails']

    def get_shared_emails(self, obj):
        return ", ".join(obj.shares.values_list('shared_with_email', flat=True))


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['id', 'text', 'author']
