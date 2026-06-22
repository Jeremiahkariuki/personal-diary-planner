"""
URL configuration for diary_planner_prj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from diary import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('diary/save/', views.save_diary_entry, name='save_diary_entry'),
    path('diary/update/<int:entry_id>/', views.update_diary_entry, name='update_diary_entry'),
    path('diary/delete/<int:entry_id>/', views.delete_diary_entry, name='delete_diary_entry'),
    path('tasks/', views.manage_tasks, name='manage_tasks'),
    path('tasks/toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('tasks/clear-pending/', views.clear_pending_tasks, name='clear_pending_tasks'),
    path('events/', views.manage_events, name='manage_events'),
    path('events/update/<int:event_id>/', views.update_event, name='update_event'),
    path('events/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('profile/', views.profile_view, name='profile'),
    path('quote/random/', views.get_random_quote, name='get_random_quote'),
    path('diary/history/', views.diary_history, name='diary_history'),
    path('export/', views.export_data, name='export_data'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
