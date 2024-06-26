# Generated by Django 3.2.25 on 2024-06-05 09:07

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0279_alter_species_regions'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='species_regions',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[(1, 'Goldfields'), (2, 'Kimberley'), (3, 'Midwest'), (4, 'Pilbara'), (5, 'South Coast'), (6, 'South West'), (7, 'Swan'), (8, 'Warren'), (9, 'Wheatbelt')], max_length=250, null=True),
        ),
    ]
