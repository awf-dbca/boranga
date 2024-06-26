# Generated by Django 3.2.25 on 2024-06-07 01:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0285_auto_20240606_1146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='occurrence',
            name='processing_status',
            field=models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('locked', 'Locked'), ('split', 'Split'), ('combine', 'Combine'), ('historical', 'Historical'), ('discarded', 'Discarded')], default='draft', max_length=30, verbose_name='Processing Status'),
        ),
    ]
