# Generated by Django 3.2.25 on 2024-07-30 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("boranga", "0379_auto_20240730_1536"),
    ]

    operations = [
        migrations.AddField(
            model_name="threatcategory",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
