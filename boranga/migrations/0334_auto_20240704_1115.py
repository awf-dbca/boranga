# Generated by Django 3.2.25 on 2024-07-04 03:15

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0333_merge_20240704_1001'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CoordinationSource',
            new_name='CoordinateSource',
        ),
        migrations.AlterModelOptions(
            name='coordinatesource',
            options={'ordering': ['name'], 'verbose_name': 'Coordinate Source', 'verbose_name_plural': 'Coordinate Sources'},
        ),
        migrations.RenameField(
            model_name='occlocation',
            old_name='coordination_source',
            new_name='coordinate_source',
        ),
        migrations.RenameField(
            model_name='ocrlocation',
            old_name='coordination_source',
            new_name='coordinate_source',
        ),
        migrations.AlterField(
            model_name='occurrencetenure',
            name='datetime_updated',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
