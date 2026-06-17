from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import DiaryEntry, Task, Event
from datetime import date

@login_required
def index(request):
    latest_entry = DiaryEntry.objects.filter(user=request.user).first()
    tasks = Task.objects.filter(user=request.user)
    upcoming_events = Event.objects.filter(user=request.user, completed=False)
    
    # Calculate mood streak (very simple version: consecutive days with entries)
    today = date.today()
    streak = 0
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-created_at')
    # This is a placeholder for a more complex streak calculation
    if entries.exists():
        streak = 5 # Placeholder for now, can implement logic later
        
    context = {
        'latest_entry': latest_entry,
        'tasks': tasks,
        'upcoming_events': upcoming_events,
        'task_count': tasks.filter(completed=False).count(),
        'event_count': upcoming_events.count(),
        'mood_streak': streak,
    }
    return render(request, 'index.html', context)

@login_required
def save_diary_entry(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        mood = request.POST.get('mood', 'neutral')
        if content:
            entry = DiaryEntry.objects.create(user=request.user, content=content, mood=mood)
            return JsonResponse({
                'status': 'success',
                'message': 'Entry saved successfully',
                'entry': {
                    'content': entry.content,
                    'mood': entry.mood,
                    'created_at': entry.created_at.strftime('%B %d, %Y %H:%M')
                }
            })
        return JsonResponse({'status': 'error', 'message': 'Content is required'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

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

@login_required
def manage_tasks(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            task = Task.objects.create(user=request.user, title=title)
            return JsonResponse({'status': 'success', 'task': {'id': task.id, 'title': task.title, 'completed': task.completed}})
    
    tasks = Task.objects.filter(user=request.user)
    return JsonResponse({'status': 'success', 'tasks': list(tasks.values())})

@login_required
def toggle_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.completed = not task.completed
        task.save()
        return JsonResponse({'status': 'success', 'completed': task.completed})
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)

@login_required
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
        return JsonResponse({'status': 'success'})
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)

@login_required
def manage_events(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        location = request.POST.get('location')
        event_time = request.POST.get('event_time')
        if title and event_time:
            event = Event.objects.create(user=request.user, title=title, location=location, event_time=event_time)
            return JsonResponse({'status': 'success', 'event': {
                'id': event.id,
                'title': event.title,
                'location': event.location,
                'time': event.event_time.strftime('%H:%M')
            }})
    
    events = Event.objects.filter(user=request.user, completed=False)
    return JsonResponse({'status': 'success', 'events': [{
        'id': e.id,
        'title': e.title,
        'location': e.location,
        'time': e.event_time.strftime('%H:%M')
    } for e in events]})
