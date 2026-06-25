import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diary_planner_prj.settings')
django.setup()

from diary.models import DiaryEntry

def list_entries():
    print(f"{'ID':<5} | {'Date':<15} | {'Image URL'}")
    print("-" * 100)
    for entry in DiaryEntry.objects.all():
        image_url = entry.image.url if entry.image else "No Image"
        print(f"{entry.id:<5} | {entry.created_at.strftime('%Y-%m-%d'):<15} | {image_url}")

if __name__ == "__main__":
    list_entries()
