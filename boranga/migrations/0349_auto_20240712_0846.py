# Generated by Django 3.2.25 on 2024-07-12 00:46

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0348_auto_20240712_0838'),
    ]

    operations = [
        migrations.AddField(
            model_name='occurrencegeometry',
            name='color',
            field=colorfield.fields.ColorField(default='#3333FF', image_field=None, max_length=25, samples=None),
        ),
        migrations.AddField(
            model_name='occurrencegeometry',
            name='stroke',
            field=colorfield.fields.ColorField(default='#0033CC', image_field=None, max_length=25, samples=None),
        ),
        migrations.AddField(
            model_name='occurrencesite',
            name='color',
            field=colorfield.fields.ColorField(default='#FF3300', image_field=None, max_length=25, samples=None),
        ),
        migrations.AddField(
            model_name='occurrencesite',
            name='stroke',
            field=colorfield.fields.ColorField(default='#CC0000', image_field=None, max_length=25, samples=None),
        ),
    ]
