from django.shortcuts import render, redirect
from django.db import models
from django.db.models import Q
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.template.loader import get_template
from xhtml2pdf import pisa
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DiaryEntry, Task, Event, Profile, Quote
from .serializers import (
    DiaryEntrySerializer, TaskSerializer, EventSerializer, 
    UserSerializer, QuoteSerializer
)
from datetime import date
import datetime
import random

@login_required
def index(request):
    latest_entry = DiaryEntry.objects.filter(user=request.user).order_by('-created_at').first()
    tasks = Task.objects.filter(user=request.user)
    upcoming_events = Event.objects.filter(user=request.user, completed=False).order_by('date', 'event_time')
    
    # Calculate mood streak (consecutive days with entries)
    today = date.today()
    streak = 0
    
    # Get all distinct entry dates for the user
    entry_dates = DiaryEntry.objects.filter(user=request.user).values_list('created_at__date', flat=True).distinct().order_by('-created_at__date')
    
    if entry_dates.exists():
        current_date = today
        # Check if they have an entry today, if not check yesterday (to allow for end-of-day entries)
        if entry_dates[0] == today:
            streak = 1
        elif entry_dates[0] == today - datetime.timedelta(days=1):
            streak = 1
            current_date = today - datetime.timedelta(days=1)
        else:
            streak = 0
            
        if streak > 0:
            for i in range(1, len(entry_dates)):
                if entry_dates[i] == current_date - datetime.timedelta(days=1):
                    streak += 1
                    current_date = entry_dates[i]
                else:
                    break
        
    context = {
        'latest_entry': latest_entry,
        'tasks': tasks,
        'upcoming_events': upcoming_events,
        'task_count': tasks.filter(completed=False).count(),
        'completed_task_count': tasks.filter(completed=True).count(),
        'event_count': upcoming_events.count(),
        'mood_streak': streak,
        'today': today,
    }
    return render(request, 'index.html', context)

# --- API ViewSets ---

class DiaryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiaryEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiaryEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        latest = self.get_queryset().first()
        if latest:
            serializer = self.get_serializer(latest)
            return Response(serializer.data)
        return Response({'detail': 'No entries found'}, status=status.HTTP_404_NOT_FOUND)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).order_by('completed', 'due_date', 'due_time', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        task = self.get_object()
        task.completed = not task.completed
        task.save()
        return Response({'status': 'success', 'completed': task.completed})

    @action(detail=False, methods=['post'], url_path='clear-pending')
    def clear_pending(self, request):
        self.get_queryset().filter(completed=False).delete()
        return Response({'status': 'success'})

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user).order_by('date', 'event_time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class QuoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def random(self, request):
        count = self.queryset.count()
        if count == 0:
            return Response({'detail': 'No quotes found'}, status=404)
        random_index = random.randint(0, count - 1)
        quote = self.queryset[random_index]
        serializer = self.get_serializer(quote)
        return Response(serializer.data)

# --- Standard Template Views ---

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- Profile & History Views ---

@login_required
def profile_view(request):
    user = request.user
    
    # Ensure profile exists
    from .models import Profile
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Aggregate stats
    entry_count = DiaryEntry.objects.filter(user=user).count()
    task_count = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, completed=True).count()
    event_count = Event.objects.filter(user=user).count()
    
    # Mood statistics
    mood_stats = []
    for mood_val, mood_label in DiaryEntry.MOOD_CHOICES:
        count = DiaryEntry.objects.filter(user=user, mood=mood_val).count()
        # Split "😊 Happy" into "😊" and "Happy"
        parts = mood_label.split(' ', 1)
        mood_stats.append({
            'emoji': parts[0] if len(parts) > 0 else '',
            'name': parts[1] if len(parts) > 1 else mood_label,
            'count': count
        })
    
    if request.method == 'POST':
        email = request.POST.get('email')
        avatar = request.FILES.get('avatar')
        
        if email:
            user.email = email
            user.save()
            
        if avatar:
            profile.avatar = avatar
            profile.save()
            
        if email or avatar:
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

    context = {
        'user': user,
        'profile': profile,
        'entry_count': entry_count,
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'event_count': event_count,
        'mood_stats': mood_stats,
    }
    return render(request, 'profile.html', context)
@login_required
def diary_history(request):
    query = request.GET.get('q')
    entries = DiaryEntry.objects.filter(user=request.user)
    if query:
        entries = entries.filter(Q(content__icontains=query) | Q(tags__name__icontains=query)).distinct()
    entries = entries.order_by('-created_at')
    return render(request, 'history.html', {'entries': entries, 'query': query})

@login_required
def write_entry(request, entry_id=None):
    from .models import Tag
    entry = None
    if entry_id:
        entry = DiaryEntry.objects.filter(user=request.user, id=entry_id).first()
        if not entry:
            return redirect('index')

    if request.method == 'POST':
        content = request.POST.get('content')
        mood = request.POST.get('mood', 'neutral')
        image = request.FILES.get('image')
        tags_str = request.POST.get('tags', '')

        if entry:
            entry.content = content
            entry.mood = mood
            if image:
                entry.image = image
            entry.save()
            messages.success(request, 'Diary entry updated!')
        else:
            entry = DiaryEntry.objects.create(
                user=request.user,
                content=content,
                mood=mood,
                image=image
            )
            messages.success(request, 'Diary entry saved!')

        # Handle tags
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            tag_objs = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(user=request.user, name=name)
                tag_objs.append(tag)
            entry.tags.set(tag_objs)
        else:
            entry.tags.clear()

        return redirect('index')

    context = {
        'entry': entry,
        'is_edit': bool(entry_id),
        'existing_tags': ",".join([t.name for t in entry.tags.all()]) if entry else ""
    }
    return render(request, 'write_entry.html', context)

@login_required
@login_required
def export_pdf(request):
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-created_at')
    tasks = Task.objects.filter(user=request.user).order_by('completed', 'due_date')
    events = Event.objects.filter(user=request.user).order_by('date', 'event_time')
    
    template_path = 'pdf_export.html'
    context = {
        'user': request.user,
        'entries': entries,
        'tasks': tasks,
        'events': events,
        'today': date.today(),
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="jdiary_archive_{request.user.username}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

