from django_ical.views import ICalFeed
from django.shortcuts import get_object_or_404
from .models import Profile, Event, Task
from datetime import datetime, time
from django.utils import timezone

class CalendarFeed(ICalFeed):
    """
    A simple calendar feed for Events and Tasks.
    """
    product_id = '-//Personal Diary Planner//Calendar//EN'
    timezone = 'UTC'
    file_name = "calendar.ics"

    def get_object(self, request, token):
        return get_object_or_404(Profile, calendar_token=token)
        
    def title(self, obj):
        return f"Calendar for {obj.user.username}"

    def items(self, obj):
        events = list(Event.objects.filter(user=obj.user).order_by('-date'))
        tasks = list(Task.objects.filter(user=obj.user).exclude(due_date__isnull=True).order_by('-due_date'))
        return events + tasks

    def item_title(self, item):
        if isinstance(item, Task) and item.completed:
            return f"✅ {item.title}"
        return item.title

    def item_description(self, item):
        if isinstance(item, Event):
            loc = f"\nLocation: {item.location}" if item.location else ""
            return f"Event{loc}"
        else:
            return item.description or "Task"

    def item_start_datetime(self, item):
        if isinstance(item, Event):
            dt = datetime.combine(item.date, item.event_time)
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        elif isinstance(item, Task):
            t = item.due_time or time(9, 0) # default to 9 AM if no time
            dt = datetime.combine(item.due_date, t)
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            
    def item_link(self, item):
        return "/"
