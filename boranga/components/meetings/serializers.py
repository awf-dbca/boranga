import logging

from rest_framework import serializers

from boranga.components.main.serializers import (
    CommunicationLogEntrySerializer,
    EmailUserSerializer,
)
from boranga.components.meetings.models import (
    AgendaItem,
    CommitteeMembers,
    Meeting,
    MeetingLogEntry,
    MeetingUserAction,
    Minutes,
)
from boranga.helpers import is_conservation_status_approver
from boranga.ledger_api_utils import retrieve_email_user

logger = logging.getLogger(__name__)


class ListMeetingSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    processing_status = serializers.CharField(source="get_processing_status_display")
    can_user_edit = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = (
            "id",
            "meeting_number",
            "start_date",
            "end_date",
            "location",
            "title",
            "processing_status",
            "can_user_edit",
        )
        datatables_always_serialize = (
            "id",
            "meeting_number",
            "start_date",
            "end_date",
            "location",
            "title",
            "processing_status",
            "can_user_edit",
        )

    def get_location(self, obj):
        if obj.location:
            return obj.location.room_name
        return ""

    def get_can_user_edit(self, obj):
        request = self.context["request"]
        return obj.can_user_edit and is_conservation_status_approver(request)


class CreateMeetingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Meeting
        fields = ("id",)
        read_only_fields = ("id",)


class ListAgendaItemSerializer(serializers.ModelSerializer):
    group_type = serializers.SerializerMethodField(read_only=True)
    conservation_status_number = serializers.SerializerMethodField(read_only=True)
    scientific_name = serializers.SerializerMethodField(read_only=True)
    community_name = serializers.SerializerMethodField(read_only=True)
    change_code = serializers.CharField(
        source="conservation_status.change_code.code", allow_null=True, read_only=True
    )

    class Meta:
        model = AgendaItem
        fields = (
            "id",
            "meeting_id",
            "group_type",
            "conservation_status_id",
            "conservation_status_number",
            "scientific_name",
            "community_name",
            "change_code",
        )

    def get_conservation_status_number(self, obj):
        if obj.conservation_status:
            return obj.conservation_status.conservation_status_number
        else:
            return ""

    def get_group_type(self, obj):
        if obj.conservation_status:
            if obj.conservation_status.application_type:
                return obj.conservation_status.application_type.name

    def get_scientific_name(self, obj):
        if obj.conservation_status:
            if obj.conservation_status.species:
                return obj.conservation_status.species.taxonomy.scientific_name
            elif obj.conservation_status.community:
                return obj.conservation_status.community.taxonomy.community_name

    def get_community_name(self, obj):
        if obj.conservation_status:
            if obj.conservation_status.community:
                return obj.conservation_status.community.taxonomy.community_name
        else:
            return ""


class AgendaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaItem
        fields = (
            "id",
            "meeting",
            "conservation_status",
            "order",
        )
        read_only_fields = ("order", "id")


class MeetingSerializer(serializers.ModelSerializer):
    processing_status_display = serializers.SerializerMethodField(read_only=True)
    submitter = serializers.SerializerMethodField(read_only=True)
    start_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    selected_committee_members = serializers.SerializerMethodField(read_only=True)
    agenda_items_arr = serializers.SerializerMethodField(read_only=True)
    user_edit_mode = serializers.SerializerMethodField()
    readonly = serializers.SerializerMethodField()
    can_user_edit = serializers.SerializerMethodField()
    can_user_add_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = (
            "id",
            "meeting_number",
            "start_date",
            "end_date",
            "location_id",
            "title",
            "meeting_type",
            "attendees",
            "committee_id",
            "selected_committee_members",
            "processing_status",
            "processing_status_display",
            "can_user_edit",
            "can_user_add_minutes",
            "lodgement_date",
            "submitter",
            "agenda_items_arr",
            "user_edit_mode",
            "readonly",
        )

    def get_processing_status_display(self, obj):
        return obj.get_processing_status_display()

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None

    def get_selected_committee_members(self, obj):
        return [m.id for m in obj.selected_committee_members.all()]

    def get_agenda_items_arr(self, obj):
        return [cs.conservation_status_id for cs in obj.agenda_items.all()]

    def get_readonly(self, obj):
        if obj.can_user_edit:
            return False

        return obj.can_user_view

    def get_user_edit_mode(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        return obj.has_user_edit_mode(request)

    def get_can_user_edit(self, obj):
        request = self.context["request"]

        if not is_conservation_status_approver(request):
            return False

        return obj.can_user_edit

    def get_can_user_add_minutes(self, obj):
        request = self.context["request"]
        return is_conservation_status_approver(request)


class SaveMeetingSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    committee_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    end_date = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Meeting
        fields = (
            "id",
            "title",
            "start_date",
            "end_date",
            "meeting_type",
            "location_id",
            "attendees",
            "committee_id",
            "processing_status",
            "submitter",
            "can_user_edit",
        )
        read_only_fields = ("id",)


class EditMeetingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Meeting
        fields = (
            "id",
            "meeting_number",
            "start_date",
            "end_date",
            "location",
            "title",
            "meeting_type",
            "attendees",
            "processing_status",
            "can_user_edit",
        )


class MeetingLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = MeetingLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class MeetingUserActionSerializer(serializers.ModelSerializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = MeetingUserAction
        fields = "__all__"

    def get_who(self, meeting_user_action):
        email_user = retrieve_email_user(meeting_user_action.who)
        fullname = email_user.get_full_name()
        return fullname


class MinutesSerializer(serializers.ModelSerializer):
    document_category_name = serializers.SerializerMethodField()
    document_sub_category_name = serializers.SerializerMethodField()

    class Meta:
        model = Minutes
        fields = (
            "id",
            "minutes_number",
            "meeting",
            "name",
            "_file",
            "description",
            "input_name",
            "uploaded_date",
            "document_category",
            "document_category_name",
            "document_sub_category",
            "document_sub_category_name",
            "visible",
        )
        read_only_fields = ("id", "minutes_number")

    def get_document_category_name(self, obj):
        if obj.document_category:
            return obj.document_category.document_category_name

    def get_document_sub_category_name(self, obj):
        if obj.document_sub_category:
            return obj.document_sub_category.document_sub_category_name


class SaveMinutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Minutes
        fields = (
            "id",
            "meeting",
            "name",
            "description",
            "input_name",
            "uploaded_date",
            "document_category",
            "document_sub_category",
        )
        read_only_fields = ("id",)

    # override save so we can include our kwargs
    def save(self, *args, **kwargs):
        # if the instance already exists, carry on as normal
        if self.instance:
            return super().save(*args, **kwargs)
        else:
            instance = Minutes()
            validated_data = self.run_validation(self.initial_data)
            for field_name in self.Meta.fields:
                if (
                    field_name in validated_data
                    and field_name not in self.Meta.read_only_fields
                ):
                    setattr(instance, field_name, validated_data[field_name])
            instance.save(*args, **kwargs)
            return instance


class CommitteeMembersSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommitteeMembers
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
        )
        read_only_fields = ("id", "email")
