# Generated by Django 3.2.25 on 2024-06-07 02:40

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('boranga', '0286_alter_occurrence_processing_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='occurrencetenure',
            options={'verbose_name': 'Occurrence Tenure', 'verbose_name_plural': 'Occurrence Tenures'},
        ),
        migrations.AlterField(
            model_name='conservationstatus',
            name='processing_status',
            field=models.CharField(choices=[('draft', 'Draft'), ('with_assessor', 'With Assessor'), ('with_referral', 'With Referral'), ('with_approver', 'With Approver'), ('ready_for_agenda', 'Ready For Agenda'), ('awaiting_applicant_respone', 'Awaiting Applicant Response'), ('awaiting_assessor_response', 'Awaiting Assessor Response'), ('awaiting_responses', 'Awaiting Responses'), ('approved', 'Approved'), ('declined', 'Declined'), ('discarded', 'Discarded'), ('delisted', 'DeListed'), ('closed', 'Closed'), ('partially_approved', 'Partially Approved'), ('partially_declined', 'Partially Declined')], default='draft', max_length=30, verbose_name='Processing Status'),
        ),
        migrations.AlterField(
            model_name='ocrhabitatcomposition',
            name='land_form',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[(1, 'Test'), (2, 'Test2')], max_length=250, null=True),
        ),
    ]
