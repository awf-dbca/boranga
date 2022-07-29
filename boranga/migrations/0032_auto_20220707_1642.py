# Generated by Django 3.2.12 on 2022-07-07 08:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0031_auto_20220707_1631'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConservationCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='None', max_length=64)),
                ('label', models.CharField(default='None', max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='ConservationChangeCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='None', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='ConservationCriteria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='ConservationList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default='None', max_length=64)),
                ('label', models.CharField(default='None', max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='ConservationStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(blank=True, max_length=512, null=True)),
                ('change_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='boranga.conservationchangecode')),
                ('conservation_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='boranga.conservationcategory')),
                ('conservation_criteria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='boranga.conservationcriteria')),
                ('conservation_list', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='boranga.conservationlist')),
            ],
        ),
        migrations.RemoveField(
            model_name='bconservationstatus',
            name='change_code',
        ),
        migrations.RemoveField(
            model_name='bconservationstatus',
            name='conservation_category',
        ),
        migrations.RemoveField(
            model_name='bconservationstatus',
            name='conservation_criteria',
        ),
        migrations.RemoveField(
            model_name='bconservationstatus',
            name='conservation_list',
        ),
        migrations.DeleteModel(
            name='BConservationCategory',
        ),
        migrations.DeleteModel(
            name='BConservationChangeCode',
        ),
        migrations.DeleteModel(
            name='BConservationCriteria',
        ),
        migrations.DeleteModel(
            name='BConservationList',
        ),
        migrations.DeleteModel(
            name='BConservationStatus',
        ),
    ]