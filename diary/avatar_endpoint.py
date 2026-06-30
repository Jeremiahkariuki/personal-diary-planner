def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.avatar = request.FILES['avatar']
        profile.save()
        return JsonResponse({'status': 'ok', 'url': profile.avatar.url})
    return JsonResponse({'error': 'Invalid request'}, status=400)
