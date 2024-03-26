import requests
import json
from datetime import timedelta, date, datetime
import pytz
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from rest_framework import serializers

from ledger_api_client.ledger_models import EmailUserRO
from boranga.components.main.serializers import EmailUserROSerializerForReferral
from ledger_api_client.managed_models import SystemGroup
from boranga.settings import GROUP_NAME_CHOICES


def retrieve_department_users():
#    try:
#        res = requests.get('{}/api/users?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        res.raise_for_status()
#        cache.set('department_users',json.loads(res.content).get('objects'),10800)
#    except:
#        raise
    dep_users = EmailUserRO.objects.filter(Q(email__endswith='@dbca.wa.gov.au')).exclude(Q(first_name=''), Q(last_name='')).order_by('first_name')
    serialiser = EmailUserROSerializerForReferral(dep_users, many=True)
    return serialiser.data


def get_department_user(email):
    try:
        res = requests.get('{}/api/users?email={}'.format(settings.CMS_URL,email), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
        res.raise_for_status()
        data = json.loads(res.content).get('objects')
        if len(data) > 0:
            return data[0]
        else:
            return None
    except:
        raise

def to_local_tz(_date):
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return _date.astimezone(local_tz)

def check_db_connection():
    """  check connection to DB exists, connect if no connection exists """
    try:
        if not connection.is_usable():
            connection.connect()
    except Exception as e:
        connection.connect()

def handle_validation_error(e):
    # if hasattr(e, 'error_dict'):
    #     raise serializers.ValidationError(repr(e.error_dict))
    # else:
    #     raise serializers.ValidationError(repr(e[0].encode('utf-8')))
    if hasattr(e, 'error_dict'):
        raise serializers.ValidationError(repr(e.error_dict))
    else:
        if hasattr(e, 'message'):
            raise serializers.ValidationError(e.message)
        else:
            raise

#def add_business_days(from_date, number_of_days):
#    """ given from_date and number_of_days, returns the next weekday date i.e. excludes Sat/Sun """
#    to_date = from_date
#    while number_of_days:
#        to_date += timedelta(1)
#        if to_date.weekday() < 5: # i.e. is not saturday or sunday
#            number_of_days -= 1
#    return to_date
#
#def get_next_weekday(from_date):
#    """ given from_date and number_of_days, returns the next weekday date i.e. excludes Sat/Sun """
#    if from_date.weekday() == 5: # i.e. Sat
#        from_date += timedelta(2)
#    elif from_date.weekday() == 6: # i.e. Sun
#        from_date += timedelta(1)
#
#    return from_date

def get_polygon_source(geometry_obj):
    from boranga.components.occurrence.models import OccurrenceReportGeometry

    source = ""

    if not geometry_obj.drawn_by:
        source = "Unknown"
    # TODO not sure if checking for submitter is right for 'Applicant' as Assessor could be the submitter as well?
    elif isinstance(geometry_obj, OccurrenceReportGeometry) and geometry_obj.drawn_by in [
        geometry_obj.occurrence_report.submitter,
    ]:
        # Polygon drawn by submitter
        source = "Applicant"
    else:
        # System group names, e.g. boranga_assessor
        system_groups = SystemGroup.objects.filter(
            name__in=[x for x in zip(*GROUP_NAME_CHOICES)][0]
        )
        # System groups member ids
        system_group_member = list(
            {
                itm
                for group in system_groups
                for itm in group.get_system_group_member_ids()
            }
        )
        if geometry_obj.drawn_by in system_group_member:
            # Polygon drawn by assessor
            source = "Assessor"

    return source


