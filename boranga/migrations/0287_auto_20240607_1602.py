# Generated by Django 3.2.25 on 2024-06-07 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0286_auto_20240607_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='occurrencetenure',
            name='historical_occurrence',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='occurrencetenure',
            name='historical_occurrence_geometry_ewkb',
            field=models.BinaryField(blank=True, editable=True, null=True),
        ),
    ]