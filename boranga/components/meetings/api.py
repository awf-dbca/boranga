import traceback
import pytz
import json
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, status, views
from rest_framework.decorators import action as detail_route, renderer_classes
from rest_framework.decorators import action as list_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from datetime import datetime
from ledger_api_client.settings_base import TIME_ZONE
from boranga import settings
from boranga import exceptions
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from boranga.helpers import is_customer, is_internal
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer
from copy import deepcopy
from django.shortcuts import render, redirect, get_object_or_404

from boranga.components.meetings.models import( 
    Meeting,
    MeetingRoom,
    MeetingUserAction,
    Minutes,
    Committee,
    CommitteeMembers,
    AgendaItem,
)

from boranga.components.meetings.serializers import(
    ListMeetingSerializer,
    CreateMeetingSerializer,
    MeetingSerializer,
    EditMeetingSerializer,
    MeetingLogEntrySerializer,
    MeetingUserActionSerializer,
    SaveMeetingSerializer,
    MinutesSerializer,
    SaveMinutesSerializer,
    CommitteeMembersSerializer,
    ListAgendaItemSerializer,
    AgendaItemSerializer,
)

from boranga.components.conservation_status.models import ConservationStatus
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO

class MeetingFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # filter_group_type
        filter_meeting_type = request.GET.get('meeting_status')
        if queryset.model is Meeting:
            if filter_meeting_type:
                #queryset = queryset.filter(species__group_type__name=filter_group_type)
                #changed to application_type (ie group_type)
                queryset = queryset

        filter_start_date = request.GET.get('filter_start_date')
        filter_end_date = request.GET.get('filter_end_date')
        # import ipdb; ipdb.set_trace()
        if queryset.model is Meeting:
            if filter_start_date:
                queryset = queryset.filter(start_date__gte=filter_start_date)

            if filter_end_date:
                queryset = queryset.filter(end_date__lte=filter_end_date)

        filter_meeting_status = request.GET.get('filter_meeting_status')
        if filter_meeting_status and not filter_meeting_status.lower() == 'all':
            if queryset.model is Meeting:
                queryset = queryset.filter(processing_status=filter_meeting_status)

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        try:
            queryset = super(MeetingFilterBackend, self).filter_queryset(request, queryset, view)
        except Exception as e:
            print(e)
        setattr(view, '_datatables_total_count', total_count)
        return queryset

# class MeetingRenderer(DatatablesRenderer):
#     def render(self, data, accepted_media_type=None, renderer_context=None):
#         if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
#             data['recordsTotal'] = renderer_context['view']._datatables_total_count
#         return super(MeetingRenderer, self).render(data, accepted_media_type, renderer_context)
    

class MeetingPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (MeetingFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    # renderer_classes = (MeetingRenderer,)
    queryset = Meeting.objects.none()
    serializer_class = ListMeetingSerializer
    page_size = 10

    def get_queryset(self):
        #request_user = self.request.user
        qs = Meeting.objects.none()

        if is_internal(self.request):
            qs = Meeting.objects.all()

        return qs
    
    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def meeting_export(self, request, *args, **kwargs):

        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        export_format = request.GET.get("export_format")
        allowed_fields = [
            "meeting_number",
            "title",
            "location",
            "start_date",
            "end_date",
            "processing_status",
        ]

        serializer = ListMeetingSerializer(
            qs, context={"request": request}, many=True
        )
        serialized_data = serializer.data

        filtered_data = []
        for obj in serialized_data:
            filtered_obj = {
                key: value for key, value in obj.items() if key in allowed_fields
            }
            filtered_data.append(filtered_obj)

        def flatten_dict(d, parent_key="", sep="_"):
            flattened_dict = {}
            for k, v in d.items():
                new_key = parent_key + sep + k if parent_key else k
                if isinstance(v, dict):
                    flattened_dict.update(flatten_dict(v, new_key, sep))
                else:
                    flattened_dict[new_key] = v
            return flattened_dict

        flattened_data = [flatten_dict(item) for item in filtered_data]
        print(flattened_data)
        df = pd.DataFrame(flattened_data)
        new_headings = [
            "Number",
            "Start Date",
            "End Date",
            "Location",
            "Title",
            "Processing Status",
        ]
        df.columns = new_headings
        column_order = [
            "Number",
            "Title",
            "Location",
            "Start Date",
            "End Date",
            "Processing Status",
        ]
        df = df[column_order]

        if export_format is not None:
            if export_format == "excel":
                buffer = BytesIO()
                workbook = Workbook()
                sheet_name = "Sheet1"
                sheet = workbook.active
                sheet.title = sheet_name

                for row in dataframe_to_rows(df, index=False, header=True):
                    sheet.append(row)
                for cell in sheet[1]:
                    cell.font = Font(bold=True)

                workbook.save(buffer)
                buffer.seek(0)
                response = HttpResponse(
                    buffer.read(), content_type="application/vnd.ms-excel"
                )
                response["Content-Disposition"] = (
                    "attachment; filename=DBCA_Meeting.xlsx"
                )
                final_response = response
                buffer.close()
                return final_response

            elif export_format == "csv":
                csv_data = df.to_csv(index=False)
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    "attachment; filename=DBCA_Meeting.csv"
                )
                response.write(csv_data)
                return response

            else:
                return Response(status=400, data="Format not valid")
    
class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.none()
    serializer_class = MeetingSerializer

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request): #user.is_authenticated():
            qs= Meeting.objects.all()
            return qs
        return Meeting.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            meeting_type=request.data.get('meeting_type')
            data = {
                'meeting_type': meeting_type,                
            }
            serializer = CreateMeetingSerializer(data= request.data)
            #serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception = True)
            instance = serializer.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',], detail=True)
    def internal_meeting(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)        
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                    raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'], detail=True)
    @renderer_classes((JSONRenderer,))
    def meeting_save(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data
                # to resolve error for serializer submitter id as object is received in request
                if request_data['submitter']:
                    request.data['submitter'] = u'{}'.format(request_data['submitter'].get('id'))
                serializer=SaveMeetingSerializer(instance, data = request_data, partial=True)

                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    saved_instance = serializer.save()
                    # add the committee selected members to the meeting
                    saved_instance.selected_committee_members.set(request_data.get('sel_committee_members_arr'))

                    instance.log_user_action(MeetingUserAction.ACTION_SAVE_MEETING.format(instance.meeting_number), request)

            return redirect(reverse('internal'))

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'], detail=True)
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.submit(request,self)
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
            # return redirect(reverse('internal'))
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
        
    @detail_route(methods=['post'], detail=True)
    def edit_meeting(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # serializer_class = self.get_serializer()
            # serializer = serializer_class(instance,context={'request':request})
            serializer = self.get_serializer(instance)
            # serializer.is_valid(raise_exception = True)
            serializer = EditMeetingSerializer(instance, data= request.data)
            serializer.is_valid(raise_exception = True)
            serializer.save()        
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                    raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    # used form the meeting Queue section datatable to show the agenda items for the meeting
    @detail_route(methods=['GET',], detail=True)
    def fetch_agenda_items(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.agenda_items.all()
            serializer = ListAgendaItemSerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
        
    @detail_route(methods=['GET',], detail=True)
    def export_agenda_items(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.agenda_items.all()
        serializer = ListAgendaItemSerializer(qs,many=True)
        export_format = request.GET.get('export_format')
        allowed_fields = ['group_type', 'scientific_name', 'conservation_status_number']
        serialized_data = serializer.data

        try:
            filtered_data = []
            for i, obj in enumerate(serialized_data):
                filtered_obj = {key: value for key, value in obj.items() if key in allowed_fields}
                filtered_obj['Number'] = i + 1  # Assign sequential numbers starting from 1
                filtered_data.append(filtered_obj)

            df = pd.DataFrame(filtered_data)
            new_headings = ['Group Type', 'Conservation Status Number', 'Scientific Name', 'Number']
            df.columns = new_headings
            column_order = ['Number', 'Group Type', 'Scientific Name', 'Conservation Status Number']
            df = df[column_order]

            if export_format is not None:
                if export_format == "excel":
                    buffer = BytesIO()
                    workbook = Workbook()
                    sheet_name = 'Sheet1'
                    sheet = workbook.active
                    sheet.title = sheet_name

                    for row in dataframe_to_rows(df, index=False, header=True):
                        sheet.append(row)
                    for cell in sheet[1]:
                        cell.font = Font(bold=True)

                    workbook.save(buffer)
                    
                    buffer.seek(0)
                    response = HttpResponse(buffer.read(), content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=DBCA_Meeting_AgendaItems.xlsx'
                    final_response = response
                    buffer.close()
                    return final_response
                
                elif export_format == "csv":
                    csv_data = df.to_csv(index=False)
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=DBCA_Meeting_AgendaItems.csv'
                    response.write(csv_data)
                    return response
                
                else:
                    return Response(status=400, data="Format not valid")
        except:
            return Response(status=500, data="Internal Server Error")
    
    # used to add the conservation status to the meeting agenda  items
    @detail_route(methods=['post'], detail=True)
    @renderer_classes((JSONRenderer,))
    def add_agenda_item(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data
                if request_data['conservation_status_id']:
                    cs = ConservationStatus.objects.get(id=request_data['conservation_status_id'])
                    instance.agenda_items.create(conservation_status=cs)
                agenda_items = [cs.conservation_status_id for cs in instance.agenda_items.all()]
            return Response(agenda_items)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    # used to remove the conservation status from the meeting agenda  items
    @detail_route(methods=['post'], detail=True)
    @renderer_classes((JSONRenderer,))
    def remove_agenda_item(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data
                if request_data['conservation_status_id']:
                    cs = ConservationStatus.objects.get(id=request_data['conservation_status_id'])
                    agenda_item = AgendaItem.objects.get(meeting=instance, conservation_status=cs)
                    agenda_item.delete()
                agenda_items = [cs.conservation_status_id for cs in instance.agenda_items.all()]
            return Response(agenda_items)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    @detail_route(methods=['GET',], detail=True)
    def minutes(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.meeting_minutes.all()
            qs = qs.order_by('-uploaded_date')
            serializer = MinutesSerializer(qs,many=True, context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    @detail_route(methods=['GET',], detail=True)
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = MeetingLogEntrySerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',], detail=True)
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                mutable=request.data._mutable
                request.data._mutable=True
                request.data['meeting'] = u'{}'.format(instance.id)
                request.data['staff'] = u'{}'.format(request.user.id)
                request.data._mutable=mutable
                serializer = MeetingLogEntrySerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create()
                    document.name = str(request.FILES[f])
                    document._file = request.FILES[f]
                    document.save()
                # End Save Documents

                return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',], detail=True)
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = MeetingUserActionSerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class GetMeetingDict(views.APIView):
    
    def get(self, request, format=None):
        location_list = []
        locations = MeetingRoom.objects.all()
        if locations:
            for option in locations:
                location_list.append({'id': option.id,
                    'name':option.room_name,
                    });
        meeting_type_list = []
        meeting_type_choices= Meeting.MEETING_TYPE_CHOICES
        for choice in meeting_type_choices:
            meeting_type_list.append({
                'id': choice[0],
                'display_name': choice[1]
            })
        status_list = []
        status_choices= Meeting.PROCESSING_STATUS_CHOICES
        for choice in status_choices:
            status_list.append({
                'id': choice[0],
                'display_name': choice[1]
            })
        committee_list = []
        committees= Committee.objects.all()
        for option in committees:
            committee_list.append({
                'id': option.id,
                'name': option.name
            })
        res_json = {
        "location_list":location_list,
        "meeting_type_list":meeting_type_list,
        "status_list":status_list,
        "committee_list":committee_list,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type='application/json')


class MinutesViewSet(viewsets.ModelViewSet):
    queryset = Minutes.objects.none()
    serializer_class = MinutesSerializer

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request): #user.is_authenticated():
            qs= Minutes.objects.all().order_by('id')
            return qs
        return Minutes.objects.none()

    @detail_route(methods=['GET',], detail=True)
    def discard(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.visible = False
            instance.save(version_user=request.user)
            instance.meeting.log_user_action(MeetingUserAction.ACTION_DISCARD_MINUTE.format(instance.minutes_number,instance.meeting.meeting_number),request)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',], detail=True)
    def reinstate(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.visible = True
            instance.save(version_user=request.user)
            serializer = self.get_serializer(instance)
            instance.meeting.log_user_action(MeetingUserAction.ACTION_REINSTATE_MINUTE.format(instance.minutes_number,instance.meeting.meeting_number),request)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = SaveMinutesSerializer(instance, data=json.loads(request.data.get('data')))
            serializer.is_valid(raise_exception=True)
            serializer.save(no_revision=True)
            instance.add_minutes_documents(request, version_user=request.user)
            instance.meeting.log_user_action(MeetingUserAction.ACTION_UPDATE_MINUTE.format(instance.minutes_number,instance.meeting.meeting_number),request)
            return Response(serializer.data)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    def create(self, request, *args, **kwargs):
        try:
            serializer = SaveMinutesSerializer(data= json.loads(request.data.get('data')))
            serializer.is_valid(raise_exception = True)
            instance = serializer.save(no_revision=True)
            instance.add_minutes_documents(request,version_user=request.user)
            instance.meeting.log_user_action(MeetingUserAction.ACTION_ADD_MINUTE.format(instance.minutes_number,instance.meeting.meeting_number),request)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class CommitteeViewSet(viewsets.ModelViewSet):
    queryset = Committee.objects.none()
    serializer_class = None

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request): #user.is_authenticated():
            qs= Committee.objects.all()
            return qs
        return Committee.objects.none()
    
    @detail_route(methods=['GET',], detail=True)
    def committee_members(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs=CommitteeMembers.objects.filter(committee=instance)
            # qs = instance.members.all()
            qs = qs.order_by('-first_name')
            serializer = CommitteeMembersSerializer(qs,many=True, context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class AgendaItemViewSet(viewsets.ModelViewSet):
    #queryset = ProposalRequirement.objects.all()
    queryset = AgendaItem.objects.none()
    serializer_class = AgendaItemSerializer

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request): #user.is_authenticated():
            qs= AgendaItem.objects.all()
            return qs
        return AgendaItem.objects.none()

    @detail_route(methods=['GET',], detail=True)
    def move_up(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.up()
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',], detail=True)
    def move_down(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.down()
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
