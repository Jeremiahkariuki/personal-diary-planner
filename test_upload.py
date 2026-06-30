import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diary_planner_prj.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from diary.models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile

c = Client()
# create a user
user, _ = User.objects.get_or_create(username='tester')
user.set_password('pass')
user.save()
c.login(username='tester', password='pass')

# dummy image
img_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
avatar = SimpleUploadedFile('test.gif', img_content, content_type='image/gif')

response = c.post('/profile/', {'avatar': avatar})
print("Response status:", response.status_code)
# check if saved
profile = Profile.objects.get(user=user)
if profile.avatar:
    print("Avatar uploaded:", profile.avatar.url)
else:
    print("Avatar NOT uploaded")
