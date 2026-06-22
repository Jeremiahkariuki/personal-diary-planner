from rest_framework import serializers
from .models import DiaryEntry, Task, Event, Profile, Quote
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class DiaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiaryEntry
        fields = ['id', 'content', 'mood', 'created_at']
        read_only_fields = ['id', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'due_date', 'due_time', 'created_at']
        read_only_fields = ['id', 'created_at']

class EventSerializer(serializers.ModelSerializer):
    time = serializers.TimeField(source='event_time', format='%H:%M')
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'location', 'time', 'date', 'completed']
        read_only_fields = ['id']

class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['id', 'text', 'author']
