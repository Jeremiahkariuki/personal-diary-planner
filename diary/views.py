from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import DiaryEntry

@login_required
def index(request):
    latest_entry = DiaryEntry.objects.filter(user=request.user).first()
    return render(request, 'index.html', {'latest_entry': latest_entry})

@login_required
def save_diary_entry(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            entry = DiaryEntry.objects.create(user=request.user, content=content)
            return JsonResponse({
                'status': 'success',
                'message': 'Entry saved successfully',
                'entry': {
                    'content': entry.content,
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
