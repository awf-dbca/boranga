# Generated by Django 3.2.25 on 2024-04-26 08:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0229_merge_20240422_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='occurrencereportdeclineddetails',
            name='occurrence_report',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='declined_details', to='boranga.occurrencereport'),
        ),
    ]
