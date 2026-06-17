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
    upcoming_events = Event.objects.filter(user=request.user, completed=False).order_by('date', 'event_time')
    
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
        'today': today,
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
        due_date = request.POST.get('due_date')
        due_time = request.POST.get('due_time')
        if title:
            task = Task.objects.create(
                user=request.user, 
                title=title,
                due_date=due_date if due_date else None,
                due_time=due_time if due_time else None
            )
            return JsonResponse({'status': 'success', 'task': {
                'id': task.id, 
                'title': task.title, 
                'completed': task.completed,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                'due_time': task.due_time.strftime('%H:%M') if task.due_time else None
            }})
    
    tasks = Task.objects.filter(user=request.user).order_by('completed', 'due_date', 'due_time', '-created_at')
    return JsonResponse({'status': 'success', 'tasks': [{
        'id': t.id,
        'title': t.title,
        'completed': t.completed,
        'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
        'due_time': t.due_time.strftime('%H:%M') if t.due_time else None
    } for t in tasks]})

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
        event_date = request.POST.get('date')
        if title and event_time and event_date:
            event = Event.objects.create(
                user=request.user, 
                title=title, 
                location=location, 
                event_time=event_time,
                date=event_date
            )
            return JsonResponse({'status': 'success', 'event': {
                'id': event.id,
                'title': event.title,
                'location': event.location,
                'time': event.event_time.strftime('%H:%M'),
                'date': event.date.strftime('%Y-%m-%d')
            }})
    
    events = Event.objects.filter(user=request.user, completed=False).order_by('date', 'event_time')
    return JsonResponse({'status': 'success', 'events': [{
        'id': e.id,
        'title': e.title,
        'location': e.location,
        'time': e.event_time.strftime('%H:%M'),
        'date': e.date.strftime('%Y-%m-%d')
    } for e in events]})
