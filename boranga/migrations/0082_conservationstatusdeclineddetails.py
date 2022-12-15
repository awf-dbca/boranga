# Generated by Django 3.2.16 on 2022-11-17 07:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0081_auto_20221109_1135'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConservationStatusDeclinedDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('officer', models.IntegerField()),
                ('reason', models.TextField(blank=True)),
                ('cc_email', models.TextField(null=True)),
                ('conservation_status', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='boranga.conservationstatus')),
            ],
        ),
    ]