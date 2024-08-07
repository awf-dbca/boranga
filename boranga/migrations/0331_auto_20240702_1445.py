# Generated by Django 3.2.25 on 2024-07-02 06:45

from django.db import migrations


def update_approval_levels(apps, schema_editor):
    ConservationStatus = apps.get_model("boranga", "ConservationStatus")
    ConservationStatus.objects.filter(approval_level="intermediate").update(
        approval_level="immediate"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("boranga", "0330_auto_20240702_1444"),
    ]

    operations = [
        migrations.RunPython(update_approval_levels),
    ]
