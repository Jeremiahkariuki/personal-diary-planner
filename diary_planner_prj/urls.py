from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from diary import views

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'diary', views.DiaryEntryViewSet, basename='api-diary')
router.register(r'tasks', views.TaskViewSet, basename='api-tasks')
router.register(r'events', views.EventViewSet, basename='api-events')
router.register(r'quotes', views.QuoteViewSet, basename='api-quotes')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Standard Template Views
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('diary/history/', views.diary_history, name='diary_history'),
    path('diary/write/', views.write_entry, name='write_entry'),
    path('diary/edit/<int:entry_id>/', views.write_entry, name='edit_entry'),
    path('export/', views.export_pdf, name='export_pdf'),

    # REST API Endpoints
    path('api/', include(router.urls)),

    # Social Auth (django-allauth)
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
