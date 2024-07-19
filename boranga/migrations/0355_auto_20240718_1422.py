# Generated by Django 3.2.25 on 2024-07-18 06:22

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0354_auto_20240717_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='buffergeometry',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='buffergeometry',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='occurrencegeometry',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='occurrencegeometry',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='occurrencereportgeometry',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='occurrencereportgeometry',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='occurrencesite',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='occurrencesite',
            name='drawn_by',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='occurrencesite',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]