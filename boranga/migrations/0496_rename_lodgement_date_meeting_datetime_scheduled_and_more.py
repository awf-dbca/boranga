# Generated by Django 5.0.9 on 2024-11-14 04:35

import django.core.files.storage
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("boranga", "0495_conservationstatus_iucn_version_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="meeting",
            old_name="lodgement_date",
            new_name="datetime_scheduled",
        ),
        migrations.AddField(
            model_name="meeting",
            name="datetime_completed",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="meeting",
            name="datetime_created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="meeting",
            name="datetime_updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]