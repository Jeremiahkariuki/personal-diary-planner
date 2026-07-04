from django.shortcuts import render, redirect
from django.db import models
from django.db.models import Q, Count
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.template.loader import get_template
from xhtml2pdf import pisa
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import DiaryEntry, Task, Event, Profile, Quote, SystemActivityLog, SharePermission, log_activity, Reminder
from .serializers import (
    DiaryEntrySerializer, TaskSerializer, EventSerializer, 
    UserSerializer, QuoteSerializer, ReminderSerializer
)
from datetime import date
import datetime
import random
import json




@login_required
def index(request):
    latest_entry = DiaryEntry.objects.filter(user=request.user).order_by('-created_at').first()
    tasks = Task.objects.filter(user=request.user)
    upcoming_events = Event.objects.filter(user=request.user, completed=False).order_by('date', 'event_time')[:5] # Limit for dashboard
    
    # Calculate mood streak
    today = date.today()
    streak = 0
    entry_dates = DiaryEntry.objects.filter(user=request.user).values_list('created_at__date', flat=True).distinct().order_by('-created_at__date')
    
    if entry_dates.exists():
        current_date = today
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
    
    # Analytics for Charts
    # 1. Task Chart (Pending vs Completed)
    pending_tasks_count = tasks.filter(completed=False).count()
    completed_tasks_count = tasks.filter(completed=True).count()
    
    # 2. Mood Trend Chart (Last 7 days)
    mood_trend_data = []
    labels = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        labels.append(day.strftime('%a'))
        # Assign numeric values to moods for the chart
        # happy: 5, excited: 4, neutral: 3, sad: 2, stressed: 1
        mood_map = {'happy': 5, 'excited': 4, 'neutral': 3, 'sad': 2, 'stressed': 1}
        day_entry = DiaryEntry.objects.filter(user=request.user, created_at__date=day).first()
        if day_entry:
            mood_trend_data.append(mood_map.get(day_entry.mood, 3))
        else:
            mood_trend_data.append(None) # Or 0/3 depending on how we want it to look
            
    context = {
        'latest_entry': latest_entry,
        'upcoming_events': upcoming_events,
        'pending_tasks': tasks.filter(completed=False)[:3],
        'task_count': pending_tasks_count,
        'completed_task_count': completed_tasks_count,
        'event_count': upcoming_events.count(),
        'mood_streak': streak,
        'today': today,
        'chart_labels': labels,
        'mood_trend': mood_trend_data,
        'task_stats': [completed_tasks_count, pending_tasks_count],
    }
    log_activity(request.user, 'dashboard_view', 'Viewed the main dashboard')
    return render(request, 'index.html', context)

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).order_by('completed', 'due_date', 'due_time', '-created_at')
    log_activity(request.user, 'task_view', f'Viewed task list ({tasks.count()} tasks)')
    return render(request, 'tasks.html', {'tasks': tasks})

# --- API ViewSets ---

class DiaryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiaryEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        whole_diary_owners = SharePermission.objects.filter(
            Q(shared_with_email=user.email) | Q(shared_with_user=user),
            share_type='whole_diary'
        ).values_list('owner', flat=True)
        specific_entry_ids = SharePermission.objects.filter(
            Q(shared_with_email=user.email) | Q(shared_with_user=user),
            share_type='specific_diary'
        ).values_list('diary_entry_id', flat=True)
        
        return DiaryEntry.objects.filter(
            Q(user=user) |
            Q(user__in=whole_diary_owners) |
            Q(id__in=specific_entry_ids)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        log_activity(self.request.user, 'diary_write', f"Wrote a new diary entry via API (mood: {instance.mood})")

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to modify this entry.")
        instance = serializer.save()
        log_activity(self.request.user, 'diary_edit', f"Updated diary entry '{instance.id}' via API (mood: {instance.mood})")

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this entry.")
        log_activity(self.request.user, 'diary_delete', f"Deleted diary entry from {instance.created_at.strftime('%Y-%m-%d')}")
        instance.delete()

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
        instance = serializer.save(user=self.request.user)
        log_activity(self.request.user, 'task_create', f"Created task: '{instance.title}'")

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'task_edit', f"Updated task: '{instance.title}'")

    def perform_destroy(self, instance):
        log_activity(self.request.user, 'task_delete', f"Deleted task: '{instance.title}'")
        instance.delete()

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        task = self.get_object()
        task.completed = not task.completed
        task.save()
        status_str = "completed" if task.completed else "reopened"
        action_type = 'task_complete' if task.completed else 'task_edit'
        log_activity(request.user, action_type, f"Marked task: '{task.title}' as {status_str}")
        return Response({'status': 'success', 'completed': task.completed})

    @action(detail=False, methods=['post'], url_path='clear-pending')
    def clear_pending(self, request):
        pending = self.get_queryset().filter(completed=False)
        count = pending.count()
        pending.delete()
        log_activity(request.user, 'task_delete', f"Cleared all pending tasks ({count} tasks deleted)")
        return Response({'status': 'success'})

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        whole_events_owners = SharePermission.objects.filter(
            Q(shared_with_email=user.email) | Q(shared_with_user=user),
            share_type='whole_events'
        ).values_list('owner', flat=True)
        specific_event_ids = SharePermission.objects.filter(
            Q(shared_with_email=user.email) | Q(shared_with_user=user),
            share_type='specific_event'
        ).values_list('event_id', flat=True)
        
        return Event.objects.filter(
            Q(user=user) |
            Q(user__in=whole_events_owners) |
            Q(id__in=specific_event_ids)
        ).distinct().order_by('date', 'event_time')

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        log_activity(self.request.user, 'event_create', f"Created event: '{instance.title}' on {instance.date}")
        self.handle_sharing(instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to modify this event.")
        instance = serializer.save()
        log_activity(self.request.user, 'event_edit', f"Updated event: '{instance.title}'")
        self.handle_sharing(instance)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this event.")
        log_activity(self.request.user, 'event_delete', f"Deleted event: '{instance.title}'")
        instance.delete()

    def handle_sharing(self, instance):
        shared_emails_str = self.request.data.get('shared_emails', '')
        emails = [email.strip() for email in shared_emails_str.split(',') if email.strip()]

        existing = set(instance.shares.values_list('shared_with_email', flat=True))
        new_emails = set(emails) - existing
        removed_emails = existing - set(emails)

        instance.shares.filter(shared_with_email__in=removed_emails).delete()

        from django.core.mail import send_mail
        from django.conf import settings

        for email in new_emails:
            matching_user = User.objects.filter(email=email).first()
            SharePermission.objects.create(
                owner=self.request.user,
                shared_with_email=email,
                shared_with_user=matching_user,
                share_type='specific_event',
                event=instance
            )
            try:
                subject = f"Event Shared with you: {instance.title}"
                message = (
                    f"Hello,\n\n"
                    f"{self.request.user.username} ({self.request.user.email}) has shared a calendar event with you:\n"
                    f"'{instance.title}' scheduled on {instance.date} at {instance.event_time}.\n\n"
                    f"Log in to check your calendar."
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL or 'noreply@jdiary.com',
                    [email],
                    fail_silently=True
                )
            except Exception:
                pass

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        event_id = self.request.query_params.get('event')
        task_id = self.request.query_params.get('task')
        diary_entry_id = self.request.query_params.get('diary_entry')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if diary_entry_id:
            queryset = queryset.filter(diary_entry_id=diary_entry_id)
            
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        target = "an item"
        if instance.diary_entry:
            target = f"diary entry #{instance.diary_entry.id}"
        elif instance.event:
            target = f"event '{instance.event.title}'"
        elif instance.task:
            target = f"task '{instance.task.title}'"
        log_activity(self.request.user, 'settings_view', f"Scheduled a reminder for {target} at {instance.reminder_time}")

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this reminder.")
        
        target = "an item"
        if instance.diary_entry:
            target = f"diary entry #{instance.diary_entry.id}"
        elif instance.event:
            target = f"event '{instance.event.title}'"
        elif instance.task:
            target = f"task '{instance.task.title}'"
        log_activity(self.request.user, 'settings_view', f"Cancelled scheduled reminder for {target}")
        instance.delete()

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
    log_activity(user, 'profile_view', 'Visited the Profile page')
    
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
def settings_view(request):
    user = request.user
    
    # Ensure profile exists
    from .models import Profile
    profile, created = Profile.objects.get_or_create(user=user)
    log_activity(user, 'settings_view', 'Visited the Settings page')
    
    password_form = PasswordChangeForm(user=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('settings_view')
            else:
                messages.error(request, 'Please correct the error(s) below in the password form.')
        else:
            email = request.POST.get('email')
            avatar = request.FILES.get('avatar')
            is_ajax = request.POST.get('ajax') == '1'
            
            print(f"[SETTINGS POST] is_ajax={is_ajax}, email={email}, avatar={avatar}")
            print(f"[SETTINGS POST] FILES keys: {list(request.FILES.keys())}")
            print(f"[SETTINGS POST] POST keys: {list(request.POST.keys())}")
            
            if email:
                user.email = email
                user.save()
                
            if avatar:
                print(f"[SETTINGS POST] Saving avatar: {avatar.name}, size={avatar.size}")
                try:
                    profile.avatar = avatar
                    profile.save()
                    print(f"[SETTINGS POST] Avatar saved OK. URL={profile.avatar.url}")
                except Exception as e:
                    import traceback
                    error_msg = f"Storage error: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
                    messages.error(request, error_msg)
                    return redirect('settings_view')
                    
            if email or avatar:
                if is_ajax:
                    avatar_url = profile.avatar.url if profile.avatar else None
                    print(f"[SETTINGS POST] Returning JSON ok, avatar_url={avatar_url}")
                    return JsonResponse({'status': 'ok', 'avatar_url': avatar_url})
                messages.success(request, 'Settings updated successfully!')
                return redirect('settings_view')
            else:
                print("[SETTINGS POST] No email or avatar found in request — nothing saved!")
            
    shares_granted = SharePermission.objects.filter(owner=user)
    shares_received = SharePermission.objects.filter(Q(shared_with_email=user.email) | Q(shared_with_user=user))

    context = {
        'user': user,
        'profile': profile,
        'password_form': password_form,
        'shares_granted': shares_granted,
        'shares_received': shares_received,
    }
    return render(request, 'settings.html', context)
@login_required
def diary_history(request):
    query = request.GET.get('q')
    entries = DiaryEntry.objects.filter(user=request.user)
    
    if query:
        entries = entries.filter(Q(content__icontains=query) | Q(tags__name__icontains=query)).distinct()
    
    entries = entries.order_by('-created_at')

    # Fetch shared entries
    whole_diary_owners = SharePermission.objects.filter(
        Q(shared_with_email=request.user.email) | Q(shared_with_user=request.user),
        share_type='whole_diary'
    ).values_list('owner', flat=True)
    specific_entry_ids = SharePermission.objects.filter(
        Q(shared_with_email=request.user.email) | Q(shared_with_user=request.user),
        share_type='specific_diary'
    ).values_list('diary_entry_id', flat=True)
    
    shared_entries = DiaryEntry.objects.filter(
        Q(user__in=whole_diary_owners) |
        Q(id__in=specific_entry_ids)
    ).distinct().order_by('-created_at')
    
    if query:
        shared_entries = shared_entries.filter(Q(content__icontains=query) | Q(tags__name__icontains=query)).distinct()
    log_activity(request.user, 'diary_view', f'Viewed diary history ({entries.count()} entries)')

    # Mood Trends Analytics
    mood_map = {'excited': 5, 'happy': 4, 'neutral': 3, 'sad': 2, 'stressed': 1}
    last_30_days = entries.order_by('created_at')[:30]
    
    mood_trend = [mood_map.get(e.mood, 3) for e in last_30_days]
    chart_labels = [e.created_at.strftime('%b %d') for e in last_30_days]
    
    # Calculate some stats for the professional hub
    total_entries = entries.count()
    favorite_mood = "Not enough data"
    if total_entries > 0:
        mood_counts = entries.values('mood').annotate(count=Count('mood')).order_by('-count')
        if mood_counts:
            favorite_mood = mood_counts[0]['mood']

    context = {
        'entries': entries,
        'shared_entries': shared_entries,
        'query': query,
        'mood_trend': mood_trend,
        'chart_labels': chart_labels,
        'total_entries': total_entries,
        'favorite_mood': favorite_mood,
    }
    return render(request, 'history.html', context)

@login_required
def events_page(request):
    log_activity(request.user, 'event_view', 'Viewed the Events calendar')
    return render(request, 'events.html')

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
            log_activity(request.user, 'diary_edit', f'Edited diary entry (mood: {mood})')
        else:
            entry = DiaryEntry.objects.create(
                user=request.user,
                content=content,
                mood=mood,
                image=image
            )
            messages.success(request, 'Diary entry saved!')
            log_activity(request.user, 'diary_write', f'Wrote a new diary entry (mood: {mood})')

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
def save_custom_quote(request):
    """AJAX POST: save user's custom pinned quote."""
    if request.method == 'POST':
        from .models import Profile
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        author = data.get('author', '').strip()
        if not text:
            return JsonResponse({'error': 'Quote text is required.'}, status=400)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.custom_quote = text
        profile.custom_quote_author = author
        profile.save()
        return JsonResponse({'status': 'ok', 'text': text, 'author': author})
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

@login_required
def delete_custom_quote(request):
    """AJAX POST: clear the user's custom quote — reverts to random."""
    if request.method == 'POST':
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.custom_quote = None
        profile.custom_quote_author = None
        profile.save()
        # Return a fresh random quote
        all_quotes = list(Quote.objects.all())
        if all_quotes:
            q = random.choice(all_quotes)
            return JsonResponse({'status': 'ok', 'text': q.text, 'author': q.author or ''})
        return JsonResponse({'status': 'ok', 'text': 'Every day is a new beginning.', 'author': ''})
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

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


@login_required
def system_history(request):
    """Show all system activity logs for the current user."""
    filter_action = request.GET.get('filter', 'all')
    logs = SystemActivityLog.objects.filter(user=request.user)

    # Category filter groups
    filter_map = {
        'login':    ['login', 'logout'],
        'diary':    ['diary_write', 'diary_edit', 'diary_view', 'diary_delete'],
        'tasks':    ['task_view', 'task_create', 'task_complete', 'task_edit', 'task_delete'],
        'events':   ['event_view', 'event_create', 'event_edit', 'event_delete'],
        'profile':  ['profile_view', 'settings_view'],
    }

    if filter_action in filter_map:
        logs = logs.filter(action__in=filter_map[filter_action])

    # Calculate count of logs by filter category for the request user
    all_user_logs = SystemActivityLog.objects.filter(user=request.user)
    
    total_count = all_user_logs.count()
    login_count = all_user_logs.filter(action__in=filter_map['login']).count()
    diary_count = all_user_logs.filter(action__in=filter_map['diary']).count()
    tasks_count = all_user_logs.filter(action__in=filter_map['tasks']).count()
    events_count = all_user_logs.filter(action__in=filter_map['events']).count()
    profile_count = all_user_logs.filter(action__in=filter_map['profile']).count()

    context = {
        'logs': logs[:200],  # cap at 200 most recent
        'active_filter': filter_action,
        'total_count': total_count,
        'login_count': login_count,
        'diary_count': diary_count,
        'tasks_count': tasks_count,
        'events_count': events_count,
        'profile_count': profile_count,
    }
    return render(request, 'system_history.html', context)


@login_required
def share_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            share_type = data.get('share_type', '').strip()
            item_id = data.get('item_id')

            if not email or not share_type:
                return JsonResponse({'error': 'Email and Share Type are required.'}, status=400)

            diary_entry = None
            event = None

            if share_type == 'specific_diary':
                diary_entry = DiaryEntry.objects.filter(user=request.user, id=item_id).first()
                if not diary_entry:
                    return JsonResponse({'error': 'Diary Entry not found.'}, status=404)
            elif share_type == 'specific_event':
                event = Event.objects.filter(user=request.user, id=item_id).first()
                if not event:
                    return JsonResponse({'error': 'Event not found.'}, status=404)

            matching_user = User.objects.filter(email=email).first()

            share, created = SharePermission.objects.get_or_create(
                owner=request.user,
                shared_with_email=email,
                share_type=share_type,
                diary_entry=diary_entry,
                event=event,
                defaults={'shared_with_user': matching_user}
            )

            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"Shared content from {request.user.username}"
            if share_type == 'whole_diary':
                message = f"Hello,\n\n{request.user.username} has shared their entire diary with you on Jdiary. Log in to check it out."
            elif share_type == 'whole_events':
                message = f"Hello,\n\n{request.user.username} has shared their entire events calendar with you on Jdiary. Log in to check it out."
            elif share_type == 'specific_diary':
                message = f"Hello,\n\n{request.user.username} has shared a diary entry with you on Jdiary. Log in to check it out."
            else:
                message = f"Hello,\n\n{request.user.username} has shared an event ('{event.title}') with you on Jdiary. Log in to check it out."

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@jdiary.com',
                [email],
                fail_silently=True
            )

            return JsonResponse({'status': 'ok', 'created': created})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)


@login_required
def update_share(request):
    """Allow owner to change the share_type of an existing whole-scope permission."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            share_id = data.get('share_id')
            new_type = data.get('share_type', '').strip()

            valid_types = ['whole_diary', 'whole_events']
            if new_type not in valid_types:
                return JsonResponse({'error': 'Invalid permission type. Only whole_diary or whole_events can be changed.'}, status=400)

            share = SharePermission.objects.filter(
                owner=request.user,
                id=share_id,
                share_type__in=valid_types   # only allow editing whole-scope shares
            ).first()

            if not share:
                return JsonResponse({'error': 'Share permission not found or cannot be edited.'}, status=404)

            share.share_type = new_type
            share.save()
            log_activity(request.user, 'share_update', f'Updated share permission #{share_id} type to {new_type}')
            return JsonResponse({'status': 'ok', 'share_type': new_type, 'share_type_display': share.get_share_type_display()})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

@login_required
def revoke_share(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            share_id = data.get('share_id')
            share = SharePermission.objects.filter(owner=request.user, id=share_id).first()
            if not share:
                return JsonResponse({'error': 'Share permission not found or unauthorized.'}, status=404)
            share.delete()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

