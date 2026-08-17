"""
Data migration: assign a fresh, unique UUID to every Profile row that currently
has a duplicate calendar_token value.

This runs BETWEEN 0019 (which added the field with a shared default) and 0020
(which makes the field unique). Without this step, 0020 fails with:

    django.db.utils.IntegrityError: could not create unique index
    "diary_profile_calendar_token_80accec4_uniq"
    DETAIL: Key (calendar_token)=(…) is duplicated.
"""

import uuid
from django.db import migrations


def assign_unique_calendar_tokens(apps, schema_editor):
    Profile = apps.get_model("diary", "Profile")
    for profile in Profile.objects.all():
        profile.calendar_token = uuid.uuid4()
        profile.save(update_fields=["calendar_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0019_profile_calendar_token"),
    ]

    operations = [
        migrations.RunPython(
            assign_unique_calendar_tokens,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
