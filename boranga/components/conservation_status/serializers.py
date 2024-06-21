import logging

from rest_framework import serializers

from boranga.components.conservation_status.models import (
    ConservationStatus,
    ConservationStatusAmendmentRequest,
    ConservationStatusAmendmentRequestDocument,
    ConservationStatusDeclinedDetails,
    ConservationStatusDocument,
    ConservationStatusIssuanceApprovalDetails,
    ConservationStatusLogEntry,
    ConservationStatusReferral,
    ConservationStatusUserAction,
)
from boranga.components.main.serializers import (
    CommunicationLogEntrySerializer,
    EmailUserSerializer,
)
from boranga.components.species_and_communities.models import CommunityTaxonomy
from boranga.components.users.serializers import SubmitterInformationSerializer
from boranga.helpers import (
    is_conservation_status_approver,
    is_conservation_status_assessor,
    is_internal_contributor,
    is_new_external_contributor,
)
from boranga.ledger_api_utils import retrieve_email_user

logger = logging.getLogger("boranga")


# Serializer used for species and communities forms
class BasicConservationStatusSerializer(serializers.ModelSerializer):
    wa_legislative_list = serializers.CharField(
        source="wa_legislative_list.code", allow_null=True
    )
    wa_legislative_category = serializers.CharField(
        source="wa_legislative_category.code", allow_null=True
    )
    wa_priority_category = serializers.CharField(
        source="wa_priority_category.code", allow_null=True
    )
    commonwealth_conservation_list = serializers.CharField(
        source="commonwealth_conservation_list.code", allow_null=True
    )
    under_review = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "conservation_status_number",
            "wa_legislative_list",
            "wa_legislative_category",
            "wa_priority_category",
            "commonwealth_conservation_list",
            "international_conservation",
            "conservation_criteria",
            "under_review",
        )
        read_only_fields = fields

    def get_under_review(self, obj):
        under_review_statuses = [
            ConservationStatus.PROCESSING_STATUS_READY_FOR_AGENDA,
        ]
        request = self.context["request"]
        if is_conservation_status_assessor(request) or is_conservation_status_approver(
            request
        ):
            under_review_statuses.append(
                ConservationStatus.PROCESSING_STATUS_WITH_ASSESSOR
            )
            under_review_statuses.append(
                ConservationStatus.PROCESSING_STATUS_WITH_REFERRAL
            )

        return ConservationStatus.objects.filter(
            species_taxonomy=obj.species_taxonomy,
            processing_status__in=under_review_statuses,
        ).exists()


class ListConservationStatusSerializer(serializers.ModelSerializer):
    scientific_name = serializers.CharField(
        source="species_taxonomy.scientific_name", allow_null=True
    )
    community_name = serializers.SerializerMethodField()
    # TODO: Add new conservation status lists/catories
    customer_status = serializers.CharField(source="get_customer_status_display")
    is_new_contributor = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "conservation_status_number",
            "group_type",
            "scientific_name",
            "community_name",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "is_new_contributor",
        )
        datatables_always_serialize = (
            "id",
            "conservation_status_number",
            "group_type",
            "scientific_name",
            "community_name",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "is_new_contributor",
        )

    def get_community_name(self, obj):
        if obj.community:
            try:
                taxonomy = CommunityTaxonomy.objects.get(community=obj.community)
                return taxonomy.community_name
            except CommunityTaxonomy.DoesNotExist:
                return ""
        return ""

    def get_is_new_contributor(self, obj):
        return is_new_external_contributor(obj.submitter)


class ListSpeciesConservationStatusSerializer(serializers.ModelSerializer):
    group_type = serializers.SerializerMethodField()
    species_number = serializers.SerializerMethodField()
    scientific_name = serializers.CharField(
        source="species_taxonomy.scientific_name", allow_null=True
    )
    common_name = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()
    phylogenetic_group = serializers.SerializerMethodField()
    wa_priority_list = serializers.CharField(
        source="wa_priority_list.code", allow_null=True
    )
    wa_priority_category = serializers.CharField(
        source="wa_priority_category.code", allow_null=True
    )
    wa_legislative_list = serializers.CharField(
        source="wa_legislative_list.code", allow_null=True
    )
    wa_legislative_category = serializers.CharField(
        source="wa_legislative_category.code", allow_null=True
    )
    commonwealth_conservation_list = serializers.CharField(
        source="commonwealth_conservation_list.code", allow_null=True
    )
    processing_status = serializers.CharField(source="get_processing_status_display")
    assessor_process = serializers.SerializerMethodField(read_only=True)
    approver_process = serializers.SerializerMethodField(read_only=True)
    assessor_edit = serializers.SerializerMethodField(read_only=True)
    internal_user_edit = serializers.SerializerMethodField(read_only=True)
    is_new_contributor = serializers.SerializerMethodField()
    change_code = serializers.CharField(
        source="change_code.code", read_only=True, allow_null=True
    )
    submitter_name = serializers.CharField(
        source="submitter_information.name", allow_null=True
    )
    submitter_category = serializers.CharField(
        source="submitter_information.submitter_category.name", allow_null=True
    )
    submitter_organisation = serializers.CharField(
        source="submitter_information.organisation", allow_null=True
    )
    assessor_name = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "conservation_status_number",
            "group_type",
            "species_number",
            "scientific_name",
            "common_name",
            "family",
            "genus",
            "phylogenetic_group",
            "wa_priority_list",
            "wa_priority_category",
            "wa_legislative_list",
            "wa_legislative_category",
            "commonwealth_conservation_list",
            "international_conservation",
            "conservation_criteria",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "assessor_process",
            "approver_process",
            "assessor_edit",
            "internal_application",
            "internal_user_edit",
            "effective_from",
            "effective_to",
            "is_new_contributor",
            "review_due_date",
            "listing_date",
            "change_code",
            "submitter_name",
            "submitter_category",
            "submitter_organisation",
            "assessor_name",
        )
        datatables_always_serialize = (
            "id",
            "conservation_status_number",
            "group_type",
            "species_number",
            "scientific_name",
            "common_name",
            "family",
            "genus",
            "phylogenetic_group",
            "wa_priority_list",
            "wa_priority_category",
            "wa_legislative_list",
            "wa_legislative_category",
            "commonwealth_conservation_list",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "assessor_process",
            "approver_process",
            "assessor_edit",
            "internal_application",
            "internal_user_edit",
            "effective_from",
            "effective_to",
            "is_new_contributor",
            "change_code",
            "submitter_name",
            "submitter_category",
            "submitter_organisation",
            "assessor_name",
        )

    def get_group_type(self, obj):
        if obj.species:
            return obj.species.group_type.name
        else:
            return (
                obj.application_type.name
            )  # if user haven't filled up the form yet(ie. species not selected)

    def get_species_number(self, obj):
        if obj.species:
            return obj.species.species_number
        return ""

    def get_common_name(self, obj):
        if obj.species:
            if obj.species.taxonomy.vernaculars:
                names_list = obj.species.taxonomy.vernaculars.all().values_list(
                    "vernacular_name", flat=True
                )
                return ",".join(names_list)
        return ""

    def get_family(self, obj):
        if obj.species:
            if obj.species.taxonomy.family_id:
                return obj.species.taxonomy.family_name
        return ""

    def get_genus(self, obj):
        if obj.species:
            if obj.species.taxonomy.genera_id:
                return obj.species.taxonomy.genera_name
        return ""

    def get_phylogenetic_group(self, obj):
        if obj.species:
            if obj.species.taxonomy.informal_groups:
                return obj.species.taxonomy.informal_groups.all().values_list(
                    "classification_system_fk_id__class_desc", flat=True
                )
        return ""

    def get_assessor_process(self, obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context["request"]
        return obj.can_officer_process and is_conservation_status_assessor(request)

    def get_approver_process(self, obj):
        request = self.context["request"]
        return obj.can_approver_process and is_conservation_status_approver(request)

    def get_assessor_edit(self, obj):
        request = self.context["request"]
        user = request.user
        if obj.can_officer_edit:
            if user in obj.allowed_assessors:
                return True
        return False

    def get_internal_user_edit(self, obj):
        request = self.context["request"]
        return (
            obj.can_user_edit
            and obj.internal_application
            and is_internal_contributor(request)
            and obj.submitter == request.user.id
        )

    def get_is_new_contributor(self, obj):
        return is_new_external_contributor(obj.submitter)

    def get_assessor_name(self, obj):
        if obj.assigned_officer:
            email_user = retrieve_email_user(obj.assigned_officer)
            return email_user.get_full_name()
        return ""


class ListCommunityConservationStatusSerializer(serializers.ModelSerializer):
    group_type = serializers.SerializerMethodField()
    community_number = serializers.SerializerMethodField()
    community_migrated_id = serializers.SerializerMethodField()
    community_name = serializers.SerializerMethodField()
    # TODO: Add new conservation status lists/catories
    processing_status = serializers.CharField(source="get_processing_status_display")
    regions = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    assessor_process = serializers.SerializerMethodField(read_only=True)
    assessor_edit = serializers.SerializerMethodField(read_only=True)
    internal_user_edit = serializers.SerializerMethodField(read_only=True)
    wa_priority_list = serializers.CharField(
        source="wa_priority_list.code", allow_null=True
    )
    wa_priority_category = serializers.CharField(
        source="wa_priority_category.code", allow_null=True
    )
    wa_legislative_list = serializers.CharField(
        source="wa_legislative_list.code", allow_null=True
    )
    wa_legislative_category = serializers.CharField(
        source="wa_legislative_category.code", allow_null=True
    )
    commonwealth_conservation_list = serializers.CharField(
        source="commonwealth_conservation_list.code", allow_null=True
    )
    change_code = serializers.CharField(
        source="change_code.code", read_only=True, allow_null=True
    )
    submitter_name = serializers.CharField(
        source="submitter_information.name", allow_null=True
    )
    submitter_category = serializers.CharField(
        source="submitter_information.submitter_category.name", allow_null=True
    )
    submitter_organisation = serializers.CharField(
        source="submitter_information.organisation", allow_null=True
    )
    assessor_name = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "conservation_status_number",
            "group_type",
            "community_number",
            "community_migrated_id",
            "community_name",
            "regions",
            "districts",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "assessor_process",
            "assessor_edit",
            "internal_application",
            "internal_user_edit",
            "wa_priority_list",
            "wa_priority_category",
            "wa_legislative_list",
            "wa_legislative_category",
            "commonwealth_conservation_list",
            "international_conservation",
            "conservation_criteria",
            "effective_from",
            "effective_to",
            "review_due_date",
            "change_code",
            "submitter_name",
            "submitter_category",
            "submitter_organisation",
            "assessor_name",
        )
        datatables_always_serialize = (
            "id",
            "conservation_status_number",
            "community_number",
            "group_type",
            "community_migrated_id",
            "community_name",
            "regions",
            "districts",
            "processing_status",
            "customer_status",
            "can_user_edit",
            "can_user_view",
            "assessor_process",
            "assessor_edit",
            "internal_application",
            "internal_user_edit",
            "wa_priority_list",
            "wa_priority_category",
            "wa_legislative_list",
            "wa_legislative_category",
            "commonwealth_conservation_list",
            "international_conservation",
            "conservation_criteria",
            "effective_from",
            "effective_to",
            "review_due_date",
            "change_code",
            "submitter_name",
            "submitter_category",
            "submitter_organisation",
            "assessor_name",
        )

    def get_group_type(self, obj):
        if obj.community:
            return obj.community.group_type.name
        else:
            return (
                obj.application_type.name
            )  # if user haven't filled up the form yet(ie. species not selected)

    def get_community_number(self, obj):
        if obj.community:
            return obj.community.community_number
        return ""

    def get_community_migrated_id(self, obj):
        if obj.community:
            try:
                taxonomy = CommunityTaxonomy.objects.get(community=obj.community)
                return taxonomy.community_migrated_id
            except CommunityTaxonomy.DoesNotExist:
                return ""
        return ""

    def get_community_name(self, obj):
        if obj.community:
            try:
                taxonomy = CommunityTaxonomy.objects.get(community=obj.community)
                return taxonomy.community_name
            except CommunityTaxonomy.DoesNotExist:
                return ""
        return ""

    def get_regions(self, obj):
        if obj.community:
            if obj.community.regions:
                #return obj.community.region.name
                regions_list = obj.community.regions.all().values_list(
                    "name", flat=True
                )
            return ",".join(regions_list)
        return ""

    def get_districts(self, obj):
        if obj.community:
            if obj.community.districts:
                #return obj.community.district.name
                districts_list = obj.community.districts.all().values_list(
                    "name", flat=True
                )
            return ",".join(districts_list)
        return ""

    def get_assessor_process(self, obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context["request"]
        return obj.can_officer_process and is_conservation_status_assessor(request)

    def get_assessor_edit(self, obj):
        request = self.context["request"]
        user = request.user
        if obj.can_officer_edit:
            if user in obj.allowed_assessors:
                return True
        return False

    def get_internal_user_edit(self, obj):
        request = self.context["request"]
        return (
            obj.can_user_edit
            and obj.internal_application
            and is_internal_contributor(request)
            and obj.submitter == request.user.id
        )

    def get_assessor_name(self, obj):
        if obj.assigned_officer:
            email_user = retrieve_email_user(obj.assigned_officer)
            return email_user.get_full_name()
        return ""


class BaseConservationStatusSerializer(serializers.ModelSerializer):
    readonly = serializers.SerializerMethodField(read_only=True)
    group_type = serializers.SerializerMethodField(read_only=True)
    group_type_id = serializers.SerializerMethodField(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "group_type",
            "group_type_id",
            "species_taxonomy_id",
            "species_id",
            "community_id",
            "conservation_status_number",
            "wa_legislative_list_id",
            "wa_legislative_category_id",
            "wa_priority_list_id",
            "wa_priority_category_id",
            "commonwealth_conservation_list_id",
            "international_conservation",
            "conservation_criteria",
            "recommended_wa_legislative_list_id",
            "recommended_wa_legislative_category_id",
            "recommended_wa_priority_list_id",
            "recommended_wa_priority_category_id",
            "recommended_commonwealth_conservation_list_id",
            "recommended_international_conservation",
            "recommended_conservation_criteria",
            "comment",
            "proposed_date",
            "lodgement_date",
            "applicant_type",
            "applicant",
            "submitter",
            "assigned_officer",
            "customer_status",
            "processing_status",
            "review_status",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "reference",
            "applicant_details",
            "assigned_officer",
            "assigned_approver",
            "allowed_assessors",
            "deficiency_data",
            "assessor_data",
            "approval_level",
            "can_view_recommended",
            "submitter_information",
        )

    def get_readonly(self, obj):
        return False

    def get_group_type(self, obj):
        if obj.species:
            return obj.species.group_type.name
        elif obj.community:
            return obj.community.group_type.name
        else:
            return obj.application_type.name

    def get_group_type_id(self, obj):
        if obj.species:
            return obj.species.group_type.id
        elif obj.community:
            return obj.community.group_type.id
        else:
            return obj.application_type.id

    # def get_conservation_criteria(self,obj):
    #     return [c.id for c in obj.conservation_criteria.all()]

    def get_processing_status(self, obj):
        return obj.get_processing_status_display()

    def get_review_status(self, obj):
        return obj.get_review_status_display()

    def get_customer_status(self, obj):
        return obj.get_customer_status_display()


class ConservationStatusSerializer(BaseConservationStatusSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter_information = SubmitterInformationSerializer(read_only=True)

    def get_readonly(self, obj):
        return obj.can_user_view

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data

        return None


class CreateConservationStatusSerializer(BaseConservationStatusSerializer):
    application_type = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "application_type",
            "internal_application",
            "submitter",
        )
        read_only_fields = (
            "id",
            "application_type",
            "submitter",
        )


class ConservationStatusProposalReferralSerializer(serializers.ModelSerializer):
    referral = serializers.SerializerMethodField()
    processing_status = serializers.CharField(source="get_processing_status_display")
    referral_comment = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusReferral
        fields = "__all__"

    def get_referral_comment(self, obj):
        return obj.referral_comment if obj.referral_comment else ""

    def get_referral(self, obj):
        referral_email_user = retrieve_email_user(obj.referral)
        serializer = EmailUserSerializer(referral_email_user)
        return serializer.data


class ConservationStatusDeclinedDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConservationStatusDeclinedDetails
        fields = "__all__"


class ConservationStatusIssuanceApprovalDetailsSerializer(serializers.ModelSerializer):
    effective_from_date = serializers.DateField(
        format="%Y-%m-%d", required=False, allow_null=True
    )

    class Meta:
        model = ConservationStatusIssuanceApprovalDetails
        fields = (
            "effective_from_date",
            "details",
            "cc_email",
        )


class CurrentConservationStatusSerializer(serializers.ModelSerializer):
    """Used in the serializer below so we can easily reference all the required fields
    for the current conservation status in the internal conservation status serializer
    without having to add lots of serializer method fields."""

    class Meta:
        model = ConservationStatus
        fields = [
            "id",
            "conservation_status_number",
            "wa_legislative_list_id",
            "wa_legislative_category_id",
            "wa_priority_list_id",
            "wa_priority_category_id",
            "commonwealth_conservation_list_id",
            "international_conservation",
            "conservation_criteria",
        ]


class InternalConservationStatusSerializer(BaseConservationStatusSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    current_assessor = serializers.SerializerMethodField()
    latest_referrals = ConservationStatusProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    assessor_mode = serializers.SerializerMethodField()
    conservationstatusdeclineddetails = ConservationStatusDeclinedDetailsSerializer()
    conservationstatusissuanceapprovaldetails = (
        ConservationStatusIssuanceApprovalDetailsSerializer()
    )
    conservation_status_approval_document = serializers.SerializerMethodField()
    internal_user_edit = serializers.SerializerMethodField(read_only=True)
    can_edit_recommended = serializers.SerializerMethodField(read_only=True)
    referrals = ConservationStatusProposalReferralSerializer(many=True)
    is_new_contributor = serializers.SerializerMethodField(read_only=True)
    internal_application = serializers.BooleanField(read_only=True)
    current_conservation_status = CurrentConservationStatusSerializer(read_only=True)
    approver_process = serializers.SerializerMethodField(read_only=True)
    submitter_information = SubmitterInformationSerializer(read_only=True)
    conservation_status_under_review = CurrentConservationStatusSerializer(
        read_only=True, allow_null=True
    )

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "group_type",
            "group_type_id",
            "species_taxonomy_id",
            "species_id",
            "community_id",
            "conservation_status_number",
            "wa_legislative_list_id",
            "wa_legislative_category_id",
            "wa_priority_list_id",
            "wa_priority_category_id",
            "commonwealth_conservation_list_id",
            "international_conservation",
            "conservation_criteria",
            "recommended_conservation_criteria",
            "comment",
            "proposed_date",
            "processing_status",
            "customer_status",
            "readonly",
            "lodgement_date",
            "listing_date",
            "review_due_date",
            "effective_from",
            "effective_to",
            "submitter",
            "applicant_type",
            "assigned_officer",
            "assigned_approver",
            "approver_process",
            "can_user_edit",
            "can_user_view",
            "current_assessor",
            "latest_referrals",
            "referrals",
            "allowed_assessors",
            "assessor_mode",
            "deficiency_data",
            "assessor_data",
            "proposed_decline_status",
            "conservationstatusdeclineddetails",
            "conservationstatusissuanceapprovaldetails",
            "internal_user_edit",
            "conservation_status_approval_document",
            "approval_level",
            "can_view_recommended",
            "can_edit_recommended",
            "internal_application",
            "is_new_contributor",
            "change_code_id",
            "current_conservation_status",
            "submitter_information",
            "conservation_status_under_review",
        )

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None

    def get_processing_status(self, obj):
        return obj.get_processing_status_display()

    def get_readonly(self, obj):
        if obj.can_user_edit:
            if obj.internal_application:
                return False
            else:
                return True
        else:
            return obj.can_user_view

    def get_current_assessor(self, obj):
        return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

    def get_assessor_mode(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        logger.debug(obj.assessor_comments_view(request))
        return {
            "assessor_mode": True,
            "has_assessor_mode": obj.has_assessor_mode(request),
            "has_unlocked_mode": obj.has_unlocked_mode(request),
            "assessor_can_assess": obj.can_assess(request),
            "assessor_level": "assessor",
            "assessor_box_view": obj.assessor_comments_view(request),
        }

    def get_internal_user_edit(self, obj):
        # Internal user here refers to an internal contributor
        request = self.context["request"]
        return (
            obj.can_user_edit
            and obj.internal_application
            and is_internal_contributor(request)
            and obj.submitter == request.user.id
        )

    def get_conservation_status_approval_document(self, obj):
        try:
            if (
                obj.conservationstatusissuanceapprovaldetails.conservation_status_approval_document
                is not None
            ):
                return [
                    obj.conservationstatusissuanceapprovaldetails.conservation_status_approval_document.name,
                    obj.conservationstatusissuanceapprovaldetails.conservation_status_approval_document._file.url,
                ]
            else:
                return (
                    obj.conservationstatusissuanceapprovaldetails.conservation_status_approval_document
                )
        except ConservationStatusIssuanceApprovalDetails.DoesNotExist:
            return None

    def get_can_edit_recommended(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        return obj.can_edit_recommended(request)

    def get_is_new_contributor(self, obj):
        return is_new_external_contributor(obj.submitter)

    def get_approver_process(self, obj):
        request = self.context["request"]
        return obj.can_approver_process and is_conservation_status_approver(request)


class InternalSpeciesConservationStatusSerializer(BaseConservationStatusSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    current_assessor = serializers.SerializerMethodField()
    latest_referrals = ConservationStatusProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    assessor_mode = serializers.SerializerMethodField()
    conservationstatusdeclineddetails = ConservationStatusDeclinedDetailsSerializer()

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "group_type",
            "species_id",
            "conservation_status_number",
            "conservation_list_id",
            "conservation_category_id",
            "conservation_criteria",
            "comment",
            "proposed_date",
            "processing_status",
            "customer_status",
            "readonly",
            "lodgement_date",
            "submitter",
            "applicant_type",
            "assigned_officer",
            "assigned_approver",
            "can_user_edit",
            "can_user_view",
            "current_assessor",
            "latest_referrals",
            "allowed_assessors",
            "assessor_mode",
            "deficiency_data",
            "assessor_data",
            "proposed_decline_status",
            "conservationstatusdeclineddetails",
            "can_view_recommended",
        )

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None

    def get_readonly(self, obj):
        return True

    def get_current_assessor(self, obj):
        return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

    def get_assessor_mode(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        return {
            "assessor_mode": True,
            "has_assessor_mode": obj.has_assessor_mode(request),
            "assessor_can_assess": obj.can_assess(request),
            "assessor_level": "assessor",
            "assessor_box_view": obj.assessor_comments_view(request),
        }


class SaveSpeciesConservationStatusSerializer(BaseConservationStatusSerializer):
    species_taxonomy_id = serializers.IntegerField(required=True, write_only=True)

    wa_legislative_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_legislative_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_priority_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_priority_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    commonwealth_conservation_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    recommended_wa_legislative_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_legislative_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_priority_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_priority_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_commonwealth_conservation_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    change_code_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "application_type",
            "species_taxonomy_id",
            "wa_legislative_list_id",
            "wa_legislative_category_id",
            "wa_priority_list_id",
            "wa_priority_category_id",
            "commonwealth_conservation_list_id",
            "international_conservation",
            "conservation_criteria",
            "recommended_wa_legislative_list_id",
            "recommended_wa_legislative_category_id",
            "recommended_wa_priority_list_id",
            "recommended_wa_priority_category_id",
            "recommended_commonwealth_conservation_list_id",
            "recommended_international_conservation",
            "recommended_conservation_criteria",
            "comment",
            "lodgement_date",
            "listing_date",
            "review_due_date",
            "applicant_type",
            "submitter",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "reference",
            "deficiency_data",
            "assessor_data",
            "change_code_id",
            "approval_level",
        )
        read_only_fields = ("id",)


class CreateSpeciesConservationStatusSerializer(BaseConservationStatusSerializer):
    class Meta:
        model = ConservationStatus
        fields = ("id",)
        read_only_fields = ("id",)


# Not used at the moment
class InternalCommunityConservationStatusSerializer(BaseConservationStatusSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    current_assessor = serializers.SerializerMethodField()
    latest_referrals = ConservationStatusProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    assessor_mode = serializers.SerializerMethodField()
    conservationstatusdeclineddetails = ConservationStatusDeclinedDetailsSerializer(
        many=True
    )

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "group_type",
            "community_id",
            "conservation_status_number",
            "conservation_list_id",
            "conservation_category_id",
            "conservation_criteria",
            "comment",
            "proposed_date",
            "processing_status",
            "customer_status",
            "readonly",
            "lodgement_date",
            "submitter",
            "applicant_type",
            "assigned_officer",
            "assigned_approver",
            "can_user_edit",
            "can_user_view",
            "current_assessor",
            "latest_referrals",
            "allowed_assessors",
            "assessor_mode",
            "deficiency_data",
            "assessor_data",
            "proposed_decline_status",
            "conservationstatusdeclineddetails",
        )

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None

    def get_readonly(self, obj):
        return True

    def get_current_assessor(self, obj):
        return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

    def get_assessor_mode(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        return {
            "assessor_mode": True,
            "has_assessor_mode": obj.has_assessor_mode(request),
            "assessor_can_assess": obj.can_assess(request),
            "assessor_level": "assessor",
            "assessor_box_view": obj.assessor_comments_view(request),
        }


class SaveCommunityConservationStatusSerializer(BaseConservationStatusSerializer):
    community_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    wa_legislative_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_legislative_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_priority_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    wa_priority_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    commonwealth_conservation_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    recommended_wa_legislative_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_legislative_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_priority_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_wa_priority_category_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    recommended_commonwealth_conservation_list_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    change_code_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = ConservationStatus
        fields = (
            "id",
            "application_type",
            "community_id",
            "wa_legislative_list_id",
            "wa_legislative_category_id",
            "wa_priority_list_id",
            "wa_priority_category_id",
            "commonwealth_conservation_list_id",
            "international_conservation",
            "conservation_criteria",
            "recommended_wa_legislative_list_id",
            "recommended_wa_legislative_category_id",
            "recommended_wa_priority_list_id",
            "recommended_wa_priority_category_id",
            "recommended_commonwealth_conservation_list_id",
            "recommended_international_conservation",
            "recommended_conservation_criteria",
            "comment",
            "lodgement_date",
            "applicant_type",
            "submitter",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "reference",
            "deficiency_data",
            "assessor_data",
            "change_code_id",
        )
        read_only_fields = ("id",)


class ConservationStatusUserActionSerializer(serializers.ModelSerializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusUserAction
        fields = "__all__"

    def get_who(self, conservation_status_user_action):
        email_user = retrieve_email_user(conservation_status_user_action.who)
        fullname = email_user.get_full_name()
        return fullname


class ConservationStatusLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class SendReferralSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=True)
    text = serializers.CharField(allow_blank=True)

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        request = self.context.get("request")
        if request.user.email == data["email"]:
            non_field_errors.append("You cannot send referral to yourself.")
        elif not data["email"]:
            non_field_errors.append("Referral not found.")

        # Raise errors
        if field_errors:
            raise serializers.ValidationError(field_errors)
        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)
        # else:
        # pass

        return data


class DTConservationStatusReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source="get_processing_status_display")
    referral_status = serializers.CharField(source="get_processing_status_display")
    conservation_status_id = serializers.IntegerField(source="conservation_status.id")
    conservation_status_lodgement_date = serializers.CharField(
        source="conservation_status.lodgement_date"
    )
    conservation_status_number = serializers.CharField(
        source="conservation_status.conservation_status_number"
    )
    referral = serializers.SerializerMethodField()
    referral_comment = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    can_user_process = serializers.SerializerMethodField()
    group_type = serializers.SerializerMethodField()

    # species related fields
    species_number = serializers.SerializerMethodField()
    scientific_name = serializers.SerializerMethodField()
    common_name = serializers.SerializerMethodField()
    # TODO: Add new conservation status lists/catories
    community_number = serializers.SerializerMethodField()
    community_migrated_id = serializers.SerializerMethodField()
    community_name = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusReferral
        fields = (
            "id",
            "processing_status",
            "referral_status",
            "conservation_status_id",
            "conservation_status_lodgement_date",
            "conservation_status_number",
            "referral",
            "submitter",
            "can_user_process",
            "lodged_on",
            "conservation_status",
            "can_be_processed",
            "document",
            "referral_text",
            "referral_comment",
            "group_type",
            "species_number",
            "scientific_name",
            "common_name",
            "community_number",
            "community_migrated_id",
            "community_name",
        )
        datatables_always_serialize = (
            "id",
            "conservation_status_id",
            "can_be_processed",
        )

    def get_referral(self, obj):
        serializer = EmailUserSerializer(retrieve_email_user(obj.referral))
        return serializer.data

    def get_referral_comment(self, obj):
        return obj.referral_comment if obj.referral_comment else ""

    def get_submitter(self, obj):
        # if obj.submitter:
        if hasattr(obj, "submitter") and obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return ""

    def get_document(self, obj):
        return [obj.document.name, obj.document._file.url] if obj.document else None

    def get_can_user_process(self, obj):
        request = self.context["request"]
        if not obj.can_be_completed:
            return False

        if not obj.assigned_officer:
            return False

        return obj.assigned_officer == request.user.id

    def get_group_type(self, obj):
        if obj.conservation_status:
            return (
                obj.conservation_status.application_type.name
            )  # if user haven't filled up the form yet(ie. species not selected)

    def get_species_number(self, obj):
        if obj.conservation_status.species:
            return obj.conservation_status.species.species_number
        return ""

    def get_scientific_name(self, obj):
        if obj.conservation_status.species:
            if obj.conservation_status.species.taxonomy:
                return obj.conservation_status.species.taxonomy.scientific_name
        return ""

    def get_common_name(self, obj):
        if obj.conservation_status.species:
            if obj.conservation_status.species.taxonomy.vernaculars:
                names_list = obj.conservation_status.species.taxonomy.vernaculars.all().values_list(
                    "vernacular_name", flat=True
                )
                return ",".join(names_list)
        return ""

    def get_community_number(self, obj):
        if obj.conservation_status.community:
            return obj.conservation_status.community.community_number
        return ""

    def get_community_migrated_id(self, obj):
        try:
            taxonomy = CommunityTaxonomy.objects.get(
                community=obj.conservation_status.community
            )
            return taxonomy.community_migrated_id
        except CommunityTaxonomy.DoesNotExist:
            return ""

    def get_community_name(self, obj):
        try:
            taxonomy = CommunityTaxonomy.objects.get(
                community=obj.conservation_status.community
            )
            return taxonomy.community_name
        except CommunityTaxonomy.DoesNotExist:
            return ""


class ConservationStatusReferralProposalSerializer(
    InternalConservationStatusSerializer
):
    def get_assessor_mode(self, obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context["request"]
        try:
            referral = ConservationStatusReferral.objects.get(
                conservation_status=obj, referral=request.user.id
            )
        except ConservationStatusReferral.DoesNotExist:
            referral = None
        return {
            "assessor_mode": True,
            "assessor_can_assess": (
                referral.can_assess_referral() if referral else None
            ),
            "assessor_level": "referral",
            "assessor_box_view": obj.assessor_comments_view(request),
        }


class ConservationStatusReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source="get_processing_status_display")
    latest_referrals = ConservationStatusProposalReferralSerializer(many=True)
    can_be_completed = serializers.BooleanField()

    class Meta:
        model = ConservationStatusReferral
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["conservation_status"] = (
            ConservationStatusReferralProposalSerializer(
                context={"request": self.context["request"]}
            )
        )


class ConservationStatusAmendmentRequestDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConservationStatusAmendmentRequestDocument
        fields = ("id", "name", "_file")
        # fields = '__all__'


class ConservationStatusAmendmentRequestSerializer(serializers.ModelSerializer):
    # reason = serializers.SerializerMethodField()
    cs_amendment_request_documents = (
        ConservationStatusAmendmentRequestDocumentSerializer(many=True, read_only=True)
    )

    class Meta:
        model = ConservationStatusAmendmentRequest
        fields = "__all__"


class ConservationStatusAmendmentRequestDisplaySerializer(serializers.ModelSerializer):
    reason = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusAmendmentRequest
        fields = "__all__"

    def get_reason(self, obj):
        # return obj.get_reason_display()
        return obj.reason.reason if obj.reason else None


class ProposedDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)


class ProposedApprovalSerializer(serializers.Serializer):
    effective_from_date = serializers.DateField()
    effective_to_date = serializers.DateField(required=False, allow_null=True)
    details = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        if (
            data.get("effective_to_date", None)
            and data["effective_to_date"] < data["effective_from_date"]
        ):
            raise serializers.ValidationError(
                {
                    "effective_to_date": "Effective to date must be greater than effective from date."
                }
            )
        return data


class ConservationStatusDocumentSerializer(serializers.ModelSerializer):
    document_category_name = serializers.SerializerMethodField()
    document_sub_category_name = serializers.SerializerMethodField()

    class Meta:
        model = ConservationStatusDocument
        fields = (
            "id",
            "document_number",
            "conservation_status",
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
            "can_submitter_access",
        )
        read_only_fields = ("id", "document_number")

    def get_document_category_name(self, obj):
        if obj.document_category:
            return obj.document_category.document_category_name

    def get_document_sub_category_name(self, obj):
        if obj.document_sub_category:
            return obj.document_sub_category.document_sub_category_name


class SaveConservationStatusDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConservationStatusDocument
        fields = (
            "id",
            "conservation_status",
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
            instance = ConservationStatusDocument()
            validated_data = self.run_validation(self.initial_data)
            for field_name in self.Meta.fields:
                if (
                    field_name in validated_data
                    and field_name not in self.Meta.read_only_fields
                ):
                    setattr(instance, field_name, validated_data[field_name])
            instance.save(*args, **kwargs)
            return instance


class InternalSaveConservationStatusDocumentSerializer(
    SaveConservationStatusDocumentSerializer
):
    class Meta:
        model = ConservationStatusDocument
        fields = SaveConservationStatusDocumentSerializer.Meta.fields + (
            "can_submitter_access",
        )
        read_only_fields = (
            SaveConservationStatusDocumentSerializer.Meta.read_only_fields
        )
