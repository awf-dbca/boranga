import json
import logging
import mimetypes
import os
import subprocess
from datetime import datetime
from io import BytesIO

import pandas as pd
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from rest_framework import mixins, serializers, status, views, viewsets
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination

from boranga.components.conservation_status.models import (
    CommonwealthConservationList,
    ConservationChangeCode,
    ConservationStatus,
    ConservationStatusUserAction,
    WALegislativeCategory,
    WALegislativeList,
    WAPriorityCategory,
    WAPriorityList,
)
from boranga.components.main.related_item import RelatedItemsSerializer
from boranga.components.main.utils import validate_threat_request
from boranga.components.occurrence.api import OCCConservationThreatFilterBackend
from boranga.components.occurrence.models import OCCConservationThreat, Occurrence
from boranga.components.occurrence.serializers import OCCConservationThreatSerializer
from boranga.components.species_and_communities.email import (
    send_species_combine_email_notification,
    send_species_split_email_notification,
)
from boranga.components.species_and_communities.models import (
    Community,
    CommunityConservationAttributes,
    CommunityDistribution,
    CommunityDocument,
    CommunityPublishingStatus,
    CommunityTaxonomy,
    CommunityUserAction,
    ConservationThreat,
    CurrentImpact,
    District,
    DocumentCategory,
    DocumentSubCategory,
    FloraRecruitmentType,
    GroupType,
    InformalGroup,
    Kingdom,
    PostFireHabitatInteraction,
    PotentialImpact,
    PotentialThreatOnset,
    Region,
    RootMorphology,
    Species,
    SpeciesConservationAttributes,
    SpeciesDistribution,
    SpeciesDocument,
    SpeciesPublishingStatus,
    SpeciesUserAction,
    Taxonomy,
    TaxonVernacular,
    ThreatAgent,
    ThreatCategory,
)
from boranga.components.species_and_communities.serializers import (
    CommunityDistributionSerializer,
    CommunityDocumentSerializer,
    CommunityLogEntrySerializer,
    CommunitySerializer,
    CommunityTaxonomySerializer,
    CommunityUserActionSerializer,
    ConservationThreatSerializer,
    CreateCommunitySerializer,
    CreateSpeciesSerializer,
    DistrictSerializer,
    InternalCommunitySerializer,
    InternalSpeciesSerializer,
    ListCommunitiesSerializer,
    ListSpeciesSerializer,
    RegionSerializer,
    SaveCommunityConservationAttributesSerializer,
    SaveCommunityDistributionSerializer,
    SaveCommunityDocumentSerializer,
    SaveCommunityPublishingStatusSerializer,
    SaveCommunitySerializer,
    SaveCommunityTaxonomySerializer,
    SaveConservationThreatSerializer,
    SaveSpeciesConservationAttributesSerializer,
    SaveSpeciesDistributionSerializer,
    SaveSpeciesDocumentSerializer,
    SaveSpeciesPublishingStatusSerializer,
    SaveSpeciesSerializer,
    SpeciesDistributionSerializer,
    SpeciesDocumentSerializer,
    SpeciesLogEntrySerializer,
    SpeciesSerializer,
    SpeciesUserActionSerializer,
    TaxonomySerializer,
)
from boranga.components.species_and_communities.utils import (
    combine_species_original_submit,
    community_form_submit,
    rename_species_original_submit,
    species_form_submit,
)
from boranga.components.users.models import SubmitterCategory
from boranga.helpers import is_internal

logger = logging.getLogger(__name__)


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        return list(obj)


class GetGroupTypeDict(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        group_type_list = []
        group_types = GroupType.objects.all()
        if group_types:
            for group in group_types:
                group_type_list.append(
                    {
                        "id": group.id,
                        "name": group.name,
                        "display": group.get_name_display(),
                    }
                )
        return Response(group_type_list)


# used for external conservation status/ occurrence report dash
class GetSpecies(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        if search_term:
            dumped_species = cache.get("get_species_data")
            species_data_cache = None
            if dumped_species is None:
                species_data_cache = Species.objects.all()
                cache.set("get_species_data", species_data_cache, 86400)
            else:
                species_data_cache = dumped_species
            # don't allow to choose species that are still in draft status
            exculde_status = ["draft"]
            data = species_data_cache.filter(
                ~Q(processing_status__in=exculde_status)
                & ~Q(taxonomy=None)
                & Q(taxonomy__scientific_name__icontains=search_term)
            ).values("id", "taxonomy__scientific_name")[:10]
            data_transform = [
                {"id": species["id"], "text": species["taxonomy__scientific_name"]}
                for species in data
            ]
            return Response({"results": data_transform})
        return Response()


# used for external conservation status/ occurrence report dash
class GetCommunities(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        if search_term:
            # don't allow to choose communities that are still in draft status
            exculde_status = ["draft"]
            data = Community.objects.filter(
                ~Q(processing_status__in=exculde_status)
                & Q(taxonomy__community_name__icontains=search_term)
            ).values("id", "taxonomy__community_name")[:10]
            data_transform = [
                {"id": community["id"], "text": community["taxonomy__community_name"]}
                for community in data
            ]
            return Response({"results": data_transform})
        return Response()


# used on dashboards and forms
class GetScientificName(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        group_type_id = request.GET.get("group_type_id", "")
        # identifies the request as for a species profile - we exclude those taxonomies already taken
        species_profile = request.GET.get("species_profile", False)
        # identifies the request as for a species profile dependent record - we only include those taxonomies in use
        has_species = request.GET.get("has_species", False)

        if not search_term:
            return Response({"results": []})

        taxonomies = Taxonomy.objects.all()

        if species_profile:
            taxonomies = taxonomies.filter(species=None)

        if has_species:
            taxonomies = taxonomies.exclude(species=None)

        taxonomies = taxonomies.filter(
            scientific_name__icontains=search_term,
        )
        if group_type_id:
            taxonomies = taxonomies.filter(kingdom_fk__grouptype=group_type_id)

        serializer = TaxonomySerializer(
            taxonomies[:10], context={"request": request}, many=True
        )
        return Response({"results": serializer.data})


class GetScientificNameByGroup(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        if search_term:
            group_type_id = request.GET.get("group_type_id", "")
            queryset = Taxonomy.objects.values_list("scientific_name", flat=True)
            queryset = (
                queryset.filter(
                    scientific_name__icontains=search_term,
                    kingdom_fk__grouptype=group_type_id,
                )
                .distinct()
                .values("id", "scientific_name")[:10]
            )
            queryset = [
                {"id": taxon["id"], "text": taxon["scientific_name"]}
                for taxon in queryset
            ]
        return Response({"results": queryset})


class GetCommonName(views.APIView):
    def get(self, request, format=None):
        group_type_id = request.GET.get("group_type_id", "")
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = TaxonVernacular.objects.filter(
                    vernacular_name__icontains=search_term,
                    taxonomy__kingdom_fk__grouptype=group_type_id,
                ).values("id", "vernacular_name")[:10]
            else:
                data = TaxonVernacular.objects.filter(
                    vernacular_name__icontains=search_term,
                    taxonomy__kingdom_fk__grouptype=group_type_id,
                ).values("id", "vernacular_name")[:10]
            data_transform = [
                {"id": vern["id"], "text": vern["vernacular_name"]} for vern in data
            ]
            return Response({"results": data_transform})
        return Response()


class GetFamily(views.APIView):
    def get(self, request, format=None):
        group_type_id = request.GET.get("group_type_id", "")
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = (
                    Taxonomy.objects.filter(
                        ~Q(family_id=None),
                        family_name__icontains=search_term,
                        kingdom_fk__grouptype=group_type_id,
                    )
                    .order_by("family_name")
                    .values("family_id", "family_name")
                    .distinct()[:10]
                )
            else:
                data = (
                    Taxonomy.objects.filter(
                        ~Q(family_id=None),
                        family_name__icontains=search_term,
                        kingdom_fk__grouptype=group_type_id,
                    )
                    .order_by("family_name")
                    .values("family_id", "family_name")
                    .distinct()[:10]
                )
            data_transform = [
                {"id": taxon["family_id"], "text": taxon["family_name"]}
                for taxon in data
            ]
            return Response({"results": data_transform})
        return Response()


class GetGenera(views.APIView):
    def get(self, request, format=None):
        group_type_id = request.GET.get("group_type_id", "")
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = (
                    Taxonomy.objects.filter(
                        ~Q(genera_id=None),
                        genera_name__icontains=search_term,
                        kingdom_fk__grouptype=group_type_id,
                    )
                    .order_by("genera_name")
                    .values("genera_id", "genera_name")
                    .distinct()[:10]
                )
            else:
                data = (
                    Taxonomy.objects.filter(
                        ~Q(genera_id=None),
                        genera_name__icontains=search_term,
                        kingdom_fk__grouptype=group_type_id,
                    )
                    .order_by("genera_name")
                    .values("genera_id", "genera_name")
                    .distinct()[:10]
                )
            data_transform = [
                {"id": taxon["genera_id"], "text": taxon["genera_name"]}
                for taxon in data
            ]
            return Response({"results": data_transform})
        return Response()


class GetPhyloGroup(views.APIView):
    def get(self, request, format=None):
        #  group_type_id  retrive as may need to use later
        group_type_id = request.GET.get("group_type_id", "")
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = (
                    InformalGroup.objects.filter(
                        classification_system_fk__class_desc__icontains=search_term,
                        taxonomy__kingdom_fk__grouptype=group_type_id,
                    )
                    .distinct()
                    .values(
                        "classification_system_fk",
                        "classification_system_fk__class_desc",
                    )[:10]
                )
            else:
                data = (
                    InformalGroup.objects.filter(
                        classification_system_fk__class_desc__icontains=search_term,
                        taxonomy__kingdom_fk__grouptype=group_type_id,
                    )
                    .distinct()
                    .values(
                        "classification_system_fk",
                        "classification_system_fk__class_desc",
                    )[:10]
                )
            data_transform = [
                {
                    "id": group["classification_system_fk"],
                    "text": group["classification_system_fk__class_desc"],
                }
                for group in data
            ]
            return Response({"results": data_transform})
        return Response()


class GetCommunityId(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = CommunityTaxonomy.objects.filter(
                    community_migrated_id__icontains=search_term
                ).values("id", "community_migrated_id")[:10]
            else:
                data = CommunityTaxonomy.objects.filter(
                    community_migrated_id__icontains=search_term
                ).values("id", "community_migrated_id")[:10]
            data_transform = [
                {"id": community["id"], "text": community["community_migrated_id"]}
                for community in data
            ]
            return Response({"results": data_transform})
        return Response()


class GetCommunityName(views.APIView):
    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        cs_referral = request.GET.get("cs_referral", "")
        # taxon_details = request.GET.get('taxon_details', '')
        cs_community = request.GET.get("cs_community", "")
        if search_term:
            if cs_referral != "":
                # TODO may need to change the query for referral
                data = CommunityTaxonomy.objects.filter(
                    community_name__icontains=search_term
                ).values("id", "community_name")[:10]
                data_transform = [
                    {"id": taxon["id"], "text": taxon["community_name"]}
                    for taxon in data
                ]
            elif cs_community != "":
                exculde_status = ["draft"]
                data = CommunityTaxonomy.objects.filter(
                    ~Q(community__processing_status__in=exculde_status)
                    & Q(community_name__icontains=search_term)
                )[:10]
                data_transform = [
                    {"id": community.community.id, "text": community.community_name}
                    for community in data
                ]
            else:
                data = CommunityTaxonomy.objects.filter(
                    community_name__icontains=search_term
                ).values("id", "community_name")[:10]
                data_transform = [
                    {"id": taxon["id"], "text": taxon["community_name"]}
                    for taxon in data
                ]
            return Response({"results": data_transform})
        return Response()


class GetSpeciesFilterDict(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        # Note: Passing flora or fauna group type will return the same data (i.e. species)
        group_type = GroupType.GROUP_TYPE_FLORA
        res_json = {
            "wa_priority_lists": WAPriorityList.get_lists_dict(group_type),
            "wa_priority_categories": WAPriorityCategory.get_categories_dict(
                group_type
            ),
            "wa_legislative_lists": WALegislativeList.get_lists_dict(group_type),
            "wa_legislative_categories": WALegislativeCategory.get_categories_dict(
                group_type
            ),
            "commonwealth_conservation_lists": CommonwealthConservationList.get_lists_dict(
                group_type
            ),
            "change_codes": ConservationChangeCode.get_filter_list(),
            "submitter_categories": SubmitterCategory.get_filter_list(),
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


class GetCommunityFilterDict(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        group_type = GroupType.GROUP_TYPE_COMMUNITY
        res_json = {
            "wa_priority_lists": WAPriorityList.get_lists_dict(group_type),
            "wa_priority_categories": WAPriorityCategory.get_categories_dict(
                group_type
            ),
            "wa_legislative_lists": WALegislativeList.get_lists_dict(group_type),
            "wa_legislative_categories": WALegislativeCategory.get_categories_dict(
                group_type
            ),
            "commonwealth_conservation_lists": CommonwealthConservationList.get_lists_dict(
                group_type
            ),
            "change_codes": ConservationChangeCode.get_filter_list(),
            "submitter_categories": SubmitterCategory.get_filter_list(),
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


class GetRegionDistrictFilterDict(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        region_list = []
        regions = Region.objects.all()
        if regions:
            for region in regions:
                region_list.append(
                    {
                        "id": region.id,
                        "name": region.name,
                    }
                )
        district_list = []
        districts = District.objects.all()
        if districts:
            for district in districts:
                district_list.append(
                    {
                        "id": district.id,
                        "name": district.name,
                        "region_id": district.region_id,
                    }
                )
        res_json = {
            "region_list": region_list,
            "district_list": district_list,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


class GetDocumentCategoriesDict(views.APIView):

    def get(self, request, format=None):
        document_category_list = []
        categories = DocumentCategory.objects.all()
        if categories:
            for option in categories:
                document_category_list.append(
                    {
                        "id": option.id,
                        "name": option.document_category_name,
                    }
                )
        document_sub_category_list = []
        sub_categories = DocumentSubCategory.objects.all()
        if sub_categories:
            for option in sub_categories:
                document_sub_category_list.append(
                    {
                        "id": option.id,
                        "name": option.document_sub_category_name,
                        "category_id": option.document_category_id,
                    }
                )
        res_json = {
            "document_category_list": document_category_list,
            "document_sub_category_list": document_sub_category_list,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


# Not used now on SpeciesProfile
class TaxonomyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Taxonomy.objects.none()
    serializer_class = TaxonomySerializer

    def get_queryset(self):
        if is_internal(self.request):
            qs = Taxonomy.objects.all()
            return qs
        return Taxonomy.objects.none()

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def taxon_names(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = TaxonomySerializer(qs, context={"request": request}, many=True)
        return Response(serializer.data)

    #  not used for species profile now
    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def flora_taxon_names(self, request, *args, **kwargs):
        qs = self.get_queryset()
        flora_kingdoms = Kingdom.objects.filter(
            grouptype__name=GroupType.GROUP_TYPE_FLORA
        ).values_list("id", flat=True)
        qs = qs.filter(kingdom_fk_id__in=flora_kingdoms)
        serializer = TaxonomySerializer(qs, context={"request": request}, many=True)
        return Response(serializer.data)

    #  not used for species profile now
    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def fauna_taxon_names(self, request, *args, **kwargs):
        qs = self.get_queryset()
        fauna_kingdoms = Kingdom.objects.filter(
            grouptype__name=GroupType.GROUP_TYPE_FAUNA
        ).values_list("id", flat=True)
        qs = qs.filter(kingdom_fk_id__in=fauna_kingdoms)
        serializer = TaxonomySerializer(qs, context={"request": request}, many=True)
        return Response(serializer.data)


class GetSpeciesProfileDict(views.APIView):
    def get(self, request, format=None):
        flora_recruitment_type_list = []
        types = FloraRecruitmentType.objects.all()
        if types:
            for option in types:
                flora_recruitment_type_list.append(
                    {
                        "id": option.id,
                        "name": option.recruitment_type,
                    }
                )
        root_morphology_list = []
        types = RootMorphology.objects.all()
        if types:
            for option in types:
                root_morphology_list.append(
                    {
                        "id": option.id,
                        "name": option.name,
                    }
                )
        post_fire_habitatat_interactions_list = []
        types = PostFireHabitatInteraction.objects.all()
        if types:
            for option in types:
                post_fire_habitatat_interactions_list.append(
                    {
                        "id": option.id,
                        "name": option.name,
                    }
                )
        res_json = {
            "flora_recruitment_type_list": flora_recruitment_type_list,
            "root_morphology_list": root_morphology_list,
            "post_fire_habitatat_interactions_list": post_fire_habitatat_interactions_list,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


# Not used now on CommunityProfile
class CommunityTaxonomyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunityTaxonomy.objects.none()
    serializer_class = CommunityTaxonomySerializer

    def get_queryset(self):
        if is_internal(self.request):
            qs = CommunityTaxonomy.objects.all()
            return qs
        return CommunityTaxonomy.objects.none()

    # not used for community profile now
    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def taxon_names(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = CommunityTaxonomySerializer(
            qs, context={"request": request}, many=True
        )
        return Response(serializer.data)


class GetCommunityProfileDict(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        post_fire_habitatat_interactions_list = []
        types = PostFireHabitatInteraction.objects.all()
        if types:
            for option in types:
                post_fire_habitatat_interactions_list.append(
                    {
                        "id": option.id,
                        "name": option.name,
                    }
                )
        res_json = {
            "post_fire_habitatat_interactions_list": post_fire_habitatat_interactions_list,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")


class SpeciesFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()
        # filter_group_type
        filter_group_type = request.POST.get("filter_group_type")
        if filter_group_type:
            queryset = queryset.filter(group_type__name=filter_group_type)
        # filter_scientific_name
        filter_scientific_name = request.POST.get("filter_scientific_name")
        if filter_scientific_name and not filter_scientific_name.lower() == "all":
            queryset = queryset.filter(taxonomy=filter_scientific_name)

        filter_common_name = request.POST.get("filter_common_name")
        if filter_common_name and not filter_common_name.lower() == "all":
            queryset = queryset.filter(taxonomy__vernaculars__id=filter_common_name)

        filter_phylogenetic_group = request.POST.get("filter_phylogenetic_group")
        if filter_phylogenetic_group and not filter_phylogenetic_group.lower() == "all":
            queryset = queryset.filter(
                taxonomy__informal_groups__classification_system_fk_id=filter_phylogenetic_group
            )

        filter_family = request.POST.get("filter_family")
        if filter_family and not filter_family.lower() == "all":
            queryset = queryset.filter(taxonomy__family_id=filter_family)

        filter_genus = request.POST.get("filter_genus")
        if filter_genus and not filter_genus.lower() == "all":
            queryset = queryset.filter(taxonomy__genera_id=filter_genus)

        filter_name_status = request.POST.get("filter_name_status")
        if filter_name_status and not filter_name_status.lower() == "all":
            queryset = queryset.filter(taxonomy__name_currency=filter_name_status)

        filter_application_status = request.POST.get("filter_application_status")
        if filter_application_status and not filter_application_status.lower() == "all":
            queryset = queryset.filter(processing_status=filter_application_status)

        filter_region = request.POST.get("filter_region")
        if filter_region and not filter_region.lower() == "all":
            queryset = queryset.filter(regions__id=filter_region)

        filter_district = request.POST.get("filter_district")
        if filter_district and not filter_district.lower() == "all":
            queryset = queryset.filter(districts__id=filter_district)

        filter_wa_legislative_list = request.POST.get("filter_wa_legislative_list")
        if (
            filter_wa_legislative_list
            and not filter_wa_legislative_list.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_legislative_list_id=filter_wa_legislative_list,
            ).distinct()

        filter_wa_legislative_category = request.POST.get(
            "filter_wa_legislative_category"
        )
        if (
            filter_wa_legislative_category
            and not filter_wa_legislative_category.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_legislative_category_id=filter_wa_legislative_category,
            ).distinct()

        filter_wa_priority_category = request.POST.get("filter_wa_priority_category")
        if (
            filter_wa_priority_category
            and not filter_wa_priority_category.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_priority_category_id=filter_wa_priority_category,
            ).distinct()

        filter_commonwealth_relevance = request.POST.get(
            "filter_commonwealth_relevance"
        )
        if filter_commonwealth_relevance == "true":
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
            ).exclude(conservation_status__commonwealth_conservation_list__isnull=True)

        filter_international_relevance = request.POST.get(
            "filter_international_relevance"
        )
        if filter_international_relevance == "true":
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
            ).exclude(conservation_status__international_conservation__isnull=True)

        filter_conservation_criteria = request.POST.get("filter_conservation_criteria")
        if filter_conservation_criteria:
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__conservation_criteria__icontains=filter_conservation_criteria,
            )

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, "_datatables_total_count", total_count)
        return queryset


class SpeciesPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SpeciesFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = (
        Species.objects.all()
        .select_related(
            "taxonomy",
            "group_type",
            "species_publishing_status",
        )
        .prefetch_related(
            "conservation_status",
        )
    )
    serializer_class = ListSpeciesSerializer
    page_size = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_internal(self.request):
            qs = qs.filter(processing_status=Species.PROCESSING_STATUS_ACTIVE).filter(
                species_publishing_status__species_public=True
            )
        return qs

    @list_route(
        methods=["GET", "POST"],
        detail=False,
    )
    def species_internal(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListSpeciesSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=["GET", "POST"],
        detail=False,
        permission_classes=[AllowAny],
    )
    def species_external(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListSpeciesSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def species_internal_export(self, request, *args, **kwargs):

        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        export_format = request.GET.get("export_format")
        allowed_fields = [
            "species_number",
            "scientific_name",
            "common_name",
            "family",
            "genus",
            "phylogenetic_group",
            "regions",
            "districts",
            "processing_status",
        ]

        serializer = ListSpeciesSerializer(qs, context={"request": request}, many=True)
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
                elif isinstance(v, QuerySet):
                    values = list(
                        v.values_list(
                            "classification_system_fk_id__class_desc", flat=True
                        )
                    )
                    flattened_dict[new_key] = ",".join(values)
                else:
                    flattened_dict[new_key] = v
            return flattened_dict

        flattened_data = [flatten_dict(item) for item in filtered_data]
        df = pd.DataFrame(flattened_data)
        new_headings = [
            "Number",
            "Scientific Name",
            "Common Name",
            "Family",
            "Genera",
            "Phylo Group(s)",
            "Region(s)",
            "District(s)",
            "Processing Status",
        ]
        df.columns = new_headings
        column_order = [
            "Number",
            "Scientific Name",
            "Common Name",
            "Phylo Group(s)",
            "Family",
            "Genera",
            "Region(s)",
            "District(s)",
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
                    "attachment; filename=DBCA_Species.xlsx"
                )
                final_response = response
                buffer.close()
                return final_response

            elif export_format == "csv":
                csv_data = df.to_csv(index=False)
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    "attachment; filename=DBCA_Species.csv"
                )
                response.write(csv_data)
                return response

            else:
                return Response(status=400, data="Format not valid")


class CommunitiesFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # filter_group_type
        filter_group_type = request.GET.get("filter_group_type")
        if filter_group_type:
            queryset = queryset.filter(group_type__name=filter_group_type)

        # filter_community_migrated_id
        filter_community_migrated_id = request.GET.get("filter_community_migrated_id")
        if (
            filter_community_migrated_id
            and not filter_community_migrated_id.lower() == "all"
        ):
            queryset = queryset.filter(taxonomy=filter_community_migrated_id)

        # filter_community_name
        filter_community_name = request.GET.get("filter_community_name")
        if filter_community_name and not filter_community_name.lower() == "all":
            queryset = queryset.filter(taxonomy=filter_community_name)

        filter_application_status = request.GET.get("filter_application_status")
        if filter_application_status and not filter_application_status.lower() == "all":
            queryset = queryset.filter(processing_status=filter_application_status)

        filter_region = request.GET.get("filter_region")
        if filter_region and not filter_region.lower() == "all":
            queryset = queryset.filter(regions__id=filter_region)

        filter_district = request.GET.get("filter_district")
        if filter_district and not filter_district.lower() == "all":
            queryset = queryset.filter(districts__id=filter_district)

        filter_wa_legislative_list = request.GET.get("filter_wa_legislative_list")
        if (
            filter_wa_legislative_list
            and not filter_wa_legislative_list.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_legislative_list_id=filter_wa_legislative_list,
            ).distinct()

        filter_wa_legislative_category = request.GET.get(
            "filter_wa_legislative_category"
        )
        if (
            filter_wa_legislative_category
            and not filter_wa_legislative_category.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_legislative_category_id=filter_wa_legislative_category,
            ).distinct()

        filter_wa_priority_category = request.GET.get("filter_wa_priority_category")
        if (
            filter_wa_priority_category
            and not filter_wa_priority_category.lower() == "all"
        ):
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__wa_priority_category_id=filter_wa_priority_category,
            ).distinct()

        filter_commonwealth_relevance = request.GET.get("filter_commonwealth_relevance")
        if filter_commonwealth_relevance == "true":
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
            ).exclude(conservation_status__commonwealth_conservation_list__isnull=True)

        filter_international_relevance = request.GET.get(
            "filter_international_relevance"
        )
        if filter_international_relevance == "true":
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
            ).exclude(conservation_status__international_conservation__isnull=True)

        filter_conservation_criteria = request.GET.get("filter_conservation_criteria")
        if filter_conservation_criteria:
            queryset = queryset.filter(
                conservation_status__processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
                conservation_status__conservation_criteria__icontains=filter_conservation_criteria,
            )

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, "_datatables_total_count", total_count)
        return queryset


class CommunitiesPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (CommunitiesFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = (
        Community.objects.all()
        .select_related(
            "taxonomy",
            "group_type",
            "community_publishing_status",
        )
        .prefetch_related("conservation_status", "regions", "districts")
    )
    serializer_class = ListCommunitiesSerializer
    page_size = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_internal(self.request):
            qs = qs.filter(processing_status=Species.PROCESSING_STATUS_ACTIVE).filter(
                community_publishing_status__community_public=True
            )
        return qs

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def communities_internal(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListCommunitiesSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
        permission_classes=[AllowAny],
    )
    def communities_external(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListCommunitiesSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def communities_internal_export(self, request, *args, **kwargs):

        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        export_format = request.GET.get("export_format")
        allowed_fields = [
            "conservation_status_number",
            "community_number",
            "community_migrated_id",
            "community_name",
            "region",
            "district",
            "conservation_list",
            "conservation_category",
            "processing_status",
        ]
        serializer = ListCommunitiesSerializer(
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
        df = pd.DataFrame(flattened_data)
        new_headings = [
            "Number",
            "Community Id",
            "Community Name",
            "Region",
            "District",
            "Processing Status",
        ]
        df.columns = new_headings

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
                    "attachment; filename=DBCA_Communities.xlsx"
                )
                final_response = response
                buffer.close()
                return final_response

            elif export_format == "csv":
                csv_data = df.to_csv(index=False)
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    "attachment; filename=DBCA_Communities.csv"
                )
                response.write(csv_data)
                return response

            else:
                return Response(status=400, data="Format not valid")


class ExternalCommunityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Community.objects.none()
    serializer_class = CommunitySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if is_internal(self.request):
            qs = Community.objects.all()
            return qs
        else:
            qs = Community.objects.filter(
                processing_status=Species.PROCESSING_STATUS_ACTIVE
            ).filter(community_publishing_status__community_public=True)
            return qs

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def threats(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.community_publishing_status.threats_public:
            raise serializers.ValidationError(
                "Threats are not publicly visible for this record"
            )
        qs = instance.community_threats.filter(visible=True)
        qs = qs.order_by("-date_observed")

        filter_backend = ConservationThreatFilterBackend()
        qs = filter_backend.filter_queryset(self.request, qs, self)

        serializer = ConservationThreatSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def public_image(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.image_doc:
            return Response(status=status.HTTP_404_NOT_FOUND)
        extension = instance.image_doc._file.path.split(".")[-1].lower()
        try:
            content_type = mimetypes.types_map["." + str(extension)]
        except KeyError:
            raise ValueError(f"File type {extension} not supported")

        return HttpResponse(instance.image_doc._file, content_type=content_type)


class ExternalSpeciesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Species.objects.all()
        .select_related(
            "taxonomy",
            "group_type",
            "species_publishing_status",
        )
        .prefetch_related(
            "conservation_status",
        )
    )
    serializer_class = SpeciesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_internal(self.request):
            qs = qs.filter(processing_status=Species.PROCESSING_STATUS_ACTIVE).filter(
                species_publishing_status__species_public=True
            )
        return qs

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def threats(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.species_publishing_status.threats_public:
            raise serializers.ValidationError(
                "Threats are not publicly visible for this record"
            )
        qs = instance.species_threats.filter(visible=True)
        qs = qs.order_by("-date_observed")

        filter_backend = ConservationThreatFilterBackend()
        qs = filter_backend.filter_queryset(self.request, qs, self)

        serializer = ConservationThreatSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def public_image(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.image_doc:
            return Response(status=status.HTTP_404_NOT_FOUND)
        extension = instance.image_doc._file.path.split(".")[-1].lower()
        try:
            content_type = mimetypes.types_map["." + str(extension)]
        except KeyError:
            raise ValueError(f"File type {extension} not supported")

        return HttpResponse(instance.image_doc._file, content_type=content_type)


class SpeciesViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = (
        Species.objects.all()
        .select_related(
            "taxonomy",
            "group_type",
            "species_publishing_status",
        )
        .prefetch_related(
            "conservation_status",
        )
    )
    serializer_class = InternalSpeciesSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_internal(self.request):
            return qs.none()
        return qs

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def internal_species(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InternalSpeciesSerializer(instance, context={"request": request})
        res_json = {"species_obj": serializer.data}
        res_json = json.dumps(res_json, cls=SetEncoder)
        return HttpResponse(res_json, content_type="application/json")

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def filter_list(self, request, *args, **kwargs):
        """Used by the Related Items dashboard filters"""
        related_type = Species.RELATED_ITEM_CHOICES
        res_json = json.dumps(related_type)
        return HttpResponse(res_json, content_type="application/json")

    @list_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def occurrence_threats(self, request, *args, **kwargs):
        if is_internal(self.request):
            instance = self.get_object()
            occurrences = Occurrence.objects.filter(species=instance).values_list(
                "id", flat=True
            )
            threats = OCCConservationThreat.objects.filter(
                occurrence_id__in=occurrences
            )
            filter_backend = OCCConservationThreatFilterBackend()
            threats = filter_backend.filter_queryset(self.request, threats, self)
            serializer = OCCConservationThreatSerializer(
                threats, many=True, context={"request": request}
            )
            return Response(serializer.data)
        return Response()

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    # gets all distinct threat sources for threats pertaining to a specific OCC
    def occurrence_threat_source_list(self, request, *args, **kwargs):
        data = []
        if is_internal(self.request):
            instance = self.get_object()
            occurrences = Occurrence.objects.filter(species=instance).values_list(
                "id", flat=True
            )

            threats = OCCConservationThreat.objects.filter(
                occurrence_id__in=occurrences
            )
            distinct_occ = threats.filter(occurrence_report_threat=None).distinct(
                "occurrence"
            )
            distinct_ocr = threats.exclude(occurrence_report_threat=None).distinct(
                "occurrence_report_threat__occurrence_report"
            )

            # format
            data = data + [
                threat.occurrence.occurrence_number for threat in distinct_occ
            ]
            data = data + [
                threat.occurrence_report_threat.occurrence_report.occurrence_report_number
                for threat in distinct_ocr
            ]

        return Response(data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def species_save(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        if request_data["submitter"]:
            request.data["submitter"] = "{}".format(request_data["submitter"].get("id"))

        regions = request_data.get("regions")
        instance.regions.clear()
        for r in regions:
            region = Region.objects.get(pk=r)
            instance.regions.add(region)

        districts = request_data.get("districts")
        instance.districts.clear()
        for d in districts:
            district = District.objects.get(pk=d)
            instance.districts.add(district)

        if request_data.get("distribution"):
            distribution_instance, created = SpeciesDistribution.objects.get_or_create(
                species=instance
            )
            serializer = SpeciesDistributionSerializer(
                distribution_instance, data=request_data.get("distribution")
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        if request_data.get("conservation_attributes"):
            conservation_attributes_instance, created = (
                SpeciesConservationAttributes.objects.get_or_create(species=instance)
            )
            serializer = SaveSpeciesConservationAttributesSerializer(
                conservation_attributes_instance,
                data=request_data.get("conservation_attributes"),
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        publishing_status_instance, created = (
            SpeciesPublishingStatus.objects.get_or_create(species=instance)
        )
        publishing_status_instance.species_public = False
        publishing_status_instance.save()
        serializer = SaveSpeciesSerializer(instance, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save(version_user=request.user)

            instance.log_user_action(
                SpeciesUserAction.ACTION_SAVE_SPECIES.format(instance.species_number),
                request,
            )

        serializer = InternalSpeciesSerializer(instance, context={"request": request})

        return Response(serializer.data)

    @detail_route(methods=["DELETE"], detail=True)
    def remove(self, request, *args, **kwargs):
        # In the case of split species, when the action button is pressed a new species is created
        # and saved to the database then if the user presses the cancel button on the modal, the
        # new species is deleted. As such I belive using the delete method is justifiable for now
        # However if we have time we can change the split action to only create the new species
        # on submit. Potential TODO
        instance = self.get_object()
        instance.remove(request)
        return Response(status.HTTP_204_NO_CONTENT)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def update_publishing_status(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        publishing_status_instance, created = (
            SpeciesPublishingStatus.objects.get_or_create(species=instance)
        )
        serializer = SaveSpeciesPublishingStatusSerializer(
            publishing_status_instance,
            data=request_data,
        )
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            if (
                instance.processing_status != "active"
                and serializer.validated_data["species_public"]
            ):
                raise serializers.ValidationError(
                    "non-active species record cannot be made public"
                )
            serializer.save()

        instance.save(version_user=request.user)

        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def species_split_save(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        if request_data["submitter"]:
            request.data["submitter"] = "{}".format(request_data["submitter"].get("id"))
        if request_data.get("distribution"):
            distribution_instance, created = SpeciesDistribution.objects.get_or_create(
                species=instance
            )
            serializer = SpeciesDistributionSerializer(
                distribution_instance, data=request_data.get("distribution")
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        if request_data.get("conservation_attributes"):
            conservation_attributes_instance, created = (
                SpeciesConservationAttributes.objects.get_or_create(species=instance)
            )
            serializer = SaveSpeciesConservationAttributesSerializer(
                conservation_attributes_instance,
                data=request_data.get("conservation_attributes"),
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        # TODO - move this to dedicated save and replace with setting to private
        if request_data.get("publishing_status"):
            publishing_status_instance, created = (
                SpeciesPublishingStatus.objects.get_or_create(species=instance)
            )
            serializer = SaveSpeciesPublishingStatusSerializer(
                publishing_status_instance,
                data=request_data.get("publishing_status"),
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        serializer = SaveSpeciesSerializer(instance, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save(version_user=request.user)

            instance.log_user_action(
                SpeciesUserAction.ACTION_SAVE_SPECIES.format(instance.species_number),
                request,
            )

        return Response()

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        instance = self.get_object()
        # instance.submit(request,self)
        species_form_submit(instance, request)
        instance.save(version_user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # used to submit the new species created while spliting
    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def split_new_species_submit(self, request, *args, **kwargs):
        instance = self.get_object()
        # instance.submit(request,self)
        species_form_submit(instance, request)
        # add parent id to new species instance
        parent_species_arr = request.data.get("parent_species")
        for species in parent_species_arr:
            species_instance = Species.objects.get(id=species.get("id"))
            instance.parent_species.add(species_instance)
        # copy/clone the original species document and create new for new split species
        instance.clone_documents(request)
        instance.clone_threats(request)
        instance.save(version_user=request.user)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # used to submit the new species created while combining
    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def combine_new_species_submit(self, request, *args, **kwargs):
        instance = self.get_object()
        # instance.submit(request,self)
        species_form_submit(instance, request)

        # copy/clone the original species document and create new for new split species
        instance.clone_documents(request)
        instance.clone_threats(request)
        instance.save(version_user=request.user)
        # add parent ids to new species instance
        parent_species_arr = request.data.get("parent_species")
        for species in parent_species_arr:
            parent_instance = Species.objects.get(id=species.get("id"))
            instance.parent_species.add(parent_instance)
            # set the original species from the combine list to historical and its conservation status to 'closed'
            combine_species_original_submit(parent_instance, request)

        #  send the combine species email notification
        send_species_combine_email_notification(request, instance)

        serializer = self.get_serializer(instance)

        return Response(serializer.data)

    # Used to submit the original species after split data is submitted
    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def change_status_historical(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.processing_status = Species.PROCESSING_STATUS_HISTORICAL

        ret1 = send_species_split_email_notification(request, instance)

        if not (settings.WORKING_FROM_HOME and settings.DEBUG) and not ret1:
            raise serializers.ValidationError(
                "Email could not be sent. Please try again later"
            )

        instance.save(version_user=request.user)

        # Log action
        instance.log_user_action(
            SpeciesUserAction.ACTION_MAKE_HISTORICAL.format(instance.species_number),
            request,
        )

        serializer = self.get_serializer(instance)

        # change current active conservation status of the original species to inactive
        # TODO if the cs of species is in middle of workflow, then?
        species_cons_status = ConservationStatus.objects.filter(
            species=instance,
            processing_status=ConservationStatus.PROCESSING_STATUS_APPROVED,
        )

        if not species_cons_status.exists():
            return Response(serializer.data)

        species_cons_status.update(
            processing_status=ConservationStatus.PROCESSING_STATUS_CLOSED,
            customer_status=ConservationStatus.PROCESSING_STATUS_CLOSED,
        )

        # add the log_user_action
        species_cons_status.log_user_action(
            ConservationStatusUserAction.ACTION_CLOSE_CONSERVATIONSTATUS.format(
                species_cons_status.conservation_status_number
            ),
            request,
        )

        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def rename_deep_copy(self, request, *args, **kwargs):
        instance = self.get_object()
        # related items to instance that needs to create for new rename instance as well
        instance_documents = SpeciesDocument.objects.filter(species=instance.id)
        instance_threats = ConservationThreat.objects.filter(species=instance.id)
        instance_conservation_attributes = SpeciesConservationAttributes.objects.filter(
            species=instance.id
        )
        instance_distribution = SpeciesDistribution.objects.filter(species=instance.id)

        # clone the species instance into new rename instance
        new_rename_instance = instance
        new_rename_instance.id = None
        new_rename_instance.taxonomy_id = None
        new_rename_instance.species_number = ""
        new_rename_instance.processing_status = "draft"
        new_rename_instance.save(version_user=request.user)

        for new_document in instance_documents:
            new_doc_instance = new_document
            new_doc_instance.species = new_rename_instance
            new_doc_instance.id = None
            new_doc_instance.document_number = ""
            new_doc_instance._file.name = (
                "boranga/species/{}/species_documents/{}".format(
                    new_rename_instance.id, new_doc_instance.name
                )
            )
            new_doc_instance.can_delete = True
            new_doc_instance.save(version_user=request.user)
            new_doc_instance.species.log_user_action(
                SpeciesUserAction.ACTION_ADD_DOCUMENT.format(
                    new_doc_instance.document_number,
                    new_doc_instance.species.species_number,
                ),
                request,
            )

            check_path = os.path.exists(
                "private-media/boranga/species/{}/species_documents/".format(
                    new_rename_instance.id
                )
            )
            if check_path is True:
                # copy documents on file system
                subprocess.call(
                    "cp -p private-media/boranga/species/{}/species_documents/{}  \
                        private-media/boranga/species/{}/species_documents/".format(
                        instance.id, new_doc_instance.name, new_rename_instance.id
                    ),
                    shell=True,
                )
            else:
                # create new directory
                os.makedirs(
                    "private-media/boranga/species/{}/species_documents/".format(
                        new_rename_instance.id
                    ),
                    mode=0o777,
                )
                # then copy documents on file system
                subprocess.call(
                    "cp -p private-media/boranga/species/{}/species_documents/{}  \
                        private-media/boranga/species/{}/species_documents/".format(
                        instance.id, new_doc_instance.name, new_rename_instance.id
                    ),
                    shell=True,
                )

        for new_threat in instance_threats:
            new_threat_instance = new_threat
            new_threat_instance.species = new_rename_instance
            new_threat_instance.id = None
            new_threat_instance.threat_number = ""
            new_threat_instance.save(version_user=request.user)
            new_threat_instance.species.log_user_action(
                SpeciesUserAction.ACTION_ADD_THREAT.format(
                    new_threat_instance.threat_number,
                    new_threat_instance.species.species_number,
                ),
                request,
            )

        for new_cons_attr in instance_conservation_attributes:
            new_cons_attr_instance = new_cons_attr
            new_cons_attr_instance.species = new_rename_instance
            new_cons_attr_instance.id = None
            new_cons_attr_instance.save()

        for new_distribution in instance_distribution:
            new_distribution.species = new_rename_instance
            new_distribution.id = None
            new_distribution.save()

        serializer = InternalSpeciesSerializer(
            new_rename_instance, context={"request": request}
        )
        res_json = {"species_obj": serializer.data}
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")

    # used to submit the new species created while combining
    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def rename_new_species_submit(self, request, *args, **kwargs):
        instance = self.get_object()
        species_form_submit(instance, request)
        # add parent ids to new species instance
        parent_species_arr = request.data.get("parent_species")
        for species in parent_species_arr:
            parent_instance = Species.objects.get(id=species.get("id"))
            instance.parent_species.add(parent_instance)
            # set the original species from the rename  to historical and its conservation status to 'closed'
            rename_species_original_submit(parent_instance, request)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = request.data
        serializer = CreateSpeciesSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            new_instance, new_returned = serializer.save(version_user=request.user)

            data = {"species_id": new_instance.id}

            # create SpeciesConservationAttributes for new instance
            serializer = SaveSpeciesConservationAttributesSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # create SpeciesDistribution for new instance
            serializer = SaveSpeciesDistributionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # create SpeciesPublishingStatus for new instance
            serializer = SaveSpeciesPublishingStatusSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(new_returned, status=status.HTTP_201_CREATED)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def discard(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.discard(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.reinstate(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def documents(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.species_documents.all()
        qs = qs.order_by("-uploaded_date")
        serializer = SpeciesDocumentSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def threats(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.species_threats.all()
        qs = qs.order_by("-date_observed")

        filter_backend = ConservationThreatFilterBackend()
        qs = filter_backend.filter_queryset(self.request, qs, self)

        serializer = ConservationThreatSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = SpeciesLogEntrySerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def add_comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        mutable = request.data._mutable
        request.data._mutable = True
        request.data["species"] = f"{instance.id}"
        request.data["staff"] = f"{request.user.id}"
        request.data._mutable = mutable
        serializer = SpeciesLogEntrySerializer(data=request.data)
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

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def action_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = SpeciesUserActionSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(methods=["get"], detail=True)
    def get_related_items(self, request, *args, **kwargs):
        instance = self.get_object()
        related_filter_type = request.GET.get("related_filter_type")
        related_items = instance.get_related_items(related_filter_type)
        serializer = RelatedItemsSerializer(related_items, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @transaction.atomic
    def upload_image(self, request, *args, **kwargs):
        instance = self.get_object()
        speciesCommunitiesImageFile = request.data.get("speciesCommunitiesImage", None)
        if not speciesCommunitiesImageFile:
            raise serializers.ValidationError("No file provided")

        instance.upload_image(speciesCommunitiesImageFile)
        instance.save(version_user=request.user)
        instance.log_user_action(
            SpeciesUserAction.ACTION_IMAGE_UPDATE.format(f"{instance.id} "),
            request,
        )
        serializer = InternalSpeciesSerializer(
            instance, context={"request": request}, partial=True
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def image_history(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(instance.image_history)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate_image(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = request.data.get("pk", None)
        if not pk:
            raise serializers.ValidationError("No pk provided")
        instance.reinstate_image(pk)
        instance.log_user_action(
            SpeciesUserAction.ACTION_IMAGE_REINSTATE.format(f"{instance.id} "),
            request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def delete_image(self, request, *args, **kwargs):
        instance = self.get_object()
        # instance.upload_image(request)
        with transaction.atomic():
            instance.image_doc = None
            instance.save(version_user=request.user)
            instance.log_user_action(
                SpeciesUserAction.ACTION_IMAGE_DELETE.format(f"{instance.id} "),
                request,
            )
        serializer = InternalSpeciesSerializer(
            instance, context={"request": request}, partial=True
        )
        return Response(serializer.data)


class CommunityViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Community.objects.none()
    serializer_class = InternalCommunitySerializer
    lookup_field = "id"

    def get_queryset(self):
        if is_internal(self.request):
            qs = Community.objects.all()
            return qs
        return Community.objects.none()

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def internal_community(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InternalCommunitySerializer(instance, context={"request": request})
        res_json = {"community_obj": serializer.data}
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def filter_list(self, request, *args, **kwargs):
        """Used by the Related Items dashboard filters"""
        related_type = Community.RELATED_ITEM_CHOICES
        res_json = json.dumps(related_type)
        return HttpResponse(res_json, content_type="application/json")

    @list_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def occurrence_threats(self, request, *args, **kwargs):
        instance = self.get_object()
        occurrences = Occurrence.objects.filter(community=instance).values_list(
            "id", flat=True
        )
        threats = OCCConservationThreat.objects.filter(occurrence_id__in=occurrences)
        filter_backend = OCCConservationThreatFilterBackend()
        threats = filter_backend.filter_queryset(self.request, threats, self)
        serializer = OCCConservationThreatSerializer(
            threats, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    # gets all distinct threat sources for threats pertaining to a specific OCC
    def occurrence_threat_source_list(self, request, *args, **kwargs):
        data = []
        if is_internal(self.request):
            instance = self.get_object()
            occurrences = Occurrence.objects.filter(community=instance).values_list(
                "id", flat=True
            )

            threats = OCCConservationThreat.objects.filter(
                occurrence_id__in=occurrences
            )
            distinct_occ = threats.filter(occurrence_report_threat=None).distinct(
                "occurrence"
            )
            distinct_ocr = threats.exclude(occurrence_report_threat=None).distinct(
                "occurrence_report_threat__occurrence_report"
            )

            # format
            data = data + [
                threat.occurrence.occurrence_number for threat in distinct_occ
            ]
            data = data + [
                threat.occurrence_report_threat.occurrence_report.occurrence_report_number
                for threat in distinct_ocr
            ]

        return Response(data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def community_save(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        if request_data["submitter"]:
            request.data["submitter"] = "{}".format(request_data["submitter"].get("id"))

        if request_data.get("taxonomy_details"):
            taxonomy_instance, created = CommunityTaxonomy.objects.get_or_create(
                community=instance
            )
            serializer = SaveCommunityTaxonomySerializer(
                taxonomy_instance, data=request_data.get("taxonomy_details")
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        if request_data.get("distribution"):
            distribution_instance, created = (
                CommunityDistribution.objects.get_or_create(community=instance)
            )
            serializer = CommunityDistributionSerializer(
                distribution_instance, data=request_data.get("distribution")
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        if request_data.get("conservation_attributes"):
            conservation_attributes_instance, created = (
                CommunityConservationAttributes.objects.get_or_create(
                    community=instance
                )
            )
            serializer = SaveCommunityConservationAttributesSerializer(
                conservation_attributes_instance,
                data=request_data.get("conservation_attributes"),
            )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                serializer.save()

        publishing_status_instance, created = (
            CommunityPublishingStatus.objects.get_or_create(community=instance)
        )
        publishing_status_instance.community_public = False
        publishing_status_instance.save()

        serializer = SaveCommunitySerializer(instance, data=request_data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save(version_user=request.user)

            instance.log_user_action(
                CommunityUserAction.ACTION_SAVE_COMMUNITY.format(
                    instance.community_number
                ),
                request,
            )

        serializer = InternalCommunitySerializer(instance, context={"request": request})

        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def update_publishing_status(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        publishing_status_instance, created = (
            CommunityPublishingStatus.objects.get_or_create(community=instance)
        )
        serializer = SaveCommunityPublishingStatusSerializer(
            publishing_status_instance,
            data=request_data,
        )
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            if (
                instance.processing_status != "active"
                and serializer.validated_data["community_public"]
            ):
                raise serializers.ValidationError(
                    "non-active community record cannot be made public"
                )
            serializer.save()

        instance.save(version_user=request.user)

        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        instance = self.get_object()
        # instance.submit(request,self)
        community_form_submit(instance, request)
        instance.save(version_user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        # return redirect(reverse('internal'))

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = request.data
        serializer = CreateCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            new_instance, new_returned = serializer.save(version_user=request.user)

            data = {"community_id": new_instance.id}
            # create CommunityTaxonomy for new instance
            serializer = SaveCommunityTaxonomySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # create CommunityDistribution for new instance
            serializer = SaveCommunityDistributionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # create CommunityConservationAttributes for new instance
            serializer = SaveCommunityConservationAttributesSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # create CommunityPublishingStatus for new instance
            serializer = SaveCommunityPublishingStatusSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(new_returned, status=status.HTTP_201_CREATED)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def discard(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.discard(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.reinstate(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def documents(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.community_documents.all()
        qs = qs.order_by("-uploaded_date")
        serializer = CommunityDocumentSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def threats(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.community_threats.all()
        qs = qs.order_by("-date_observed")
        filter_backend = ConservationThreatFilterBackend()
        qs = filter_backend.filter_queryset(self.request, qs, self)
        serializer = ConservationThreatSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(methods=["get"], detail=True)
    def get_related_items(self, request, *args, **kwargs):
        instance = self.get_object()
        related_filter_type = request.GET.get("related_filter_type")
        related_items = instance.get_related_items(related_filter_type)
        serializer = RelatedItemsSerializer(related_items, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = CommunityLogEntrySerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    @transaction.atomic
    def add_comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        mutable = request.data._mutable
        request.data._mutable = True
        request.data["community"] = f"{instance.id}"
        request.data["staff"] = f"{request.user.id}"
        request.data._mutable = mutable
        serializer = CommunityLogEntrySerializer(data=request.data)
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

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def action_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = CommunityUserActionSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @transaction.atomic
    def upload_image(self, request, *args, **kwargs):
        instance = self.get_object()
        speciesCommunitiesImageFile = request.data.get("speciesCommunitiesImage", None)
        if not speciesCommunitiesImageFile:
            raise serializers.ValidationError("No file provided")

        instance.upload_image(speciesCommunitiesImageFile)
        instance.save(version_user=request.user)
        instance.log_user_action(
            CommunityUserAction.ACTION_IMAGE_UPDATE.format(f"{instance.id} "),
            request,
        )
        serializer = InternalCommunitySerializer(
            instance, context={"request": request}, partial=True
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def image_history(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(instance.image_history)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate_image(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = request.data.get("pk", None)
        if not pk:
            raise serializers.ValidationError("No pk provided")
        instance.reinstate_image(pk)
        instance.log_user_action(
            CommunityUserAction.ACTION_IMAGE_REINSTATE.format(f"{instance.id} "),
            request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def delete_image(self, request, *args, **kwargs):
        instance = self.get_object()
        # import ipdb; ipdb.set_trace()
        # instance.upload_image(request)
        with transaction.atomic():
            instance.image_doc = None
            instance.save(version_user=request.user)
            instance.log_user_action(
                CommunityUserAction.ACTION_IMAGE_DELETE.format(f"{instance.id} "),
                request,
            )
        serializer = InternalCommunitySerializer(
            instance, context={"request": request}, partial=True
        )
        return Response(serializer.data)


class SpeciesDocumentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = SpeciesDocument.objects.none()
    serializer_class = SpeciesDocumentSerializer

    def get_queryset(self):
        if is_internal(self.request):
            qs = SpeciesDocument.objects.all().order_by("id")
            return qs
        return SpeciesDocument.objects.none()

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def discard(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.visible = False
        instance.save(version_user=request.user)
        instance.species.log_user_action(
            SpeciesUserAction.ACTION_DISCARD_DOCUMENT.format(
                instance.document_number, instance.species.species_number
            ),
            request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.visible = True
        instance.save(version_user=request.user)
        serializer = self.get_serializer(instance)
        instance.species.log_user_action(
            SpeciesUserAction.ACTION_REINSTATE_DOCUMENT.format(
                instance.document_number, instance.species.species_number
            ),
            request,
        )
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SaveSpeciesDocumentSerializer(
            instance, data=json.loads(request.data.get("data"))
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(no_revision=True)
        instance.add_documents(request, version_user=request.user)
        instance.species.log_user_action(
            SpeciesUserAction.ACTION_UPDATE_DOCUMENT.format(
                instance.document_number, instance.species.species_number
            ),
            request,
        )
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = SaveSpeciesDocumentSerializer(
            data=json.loads(request.data.get("data"))
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(no_revision=True)
        instance.add_documents(request, version_user=request.user)
        instance.species.log_user_action(
            SpeciesUserAction.ACTION_ADD_DOCUMENT.format(
                instance.document_number, instance.species.species_number
            ),
            request,
        )
        return Response(serializer.data)


class CommunityDocumentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = CommunityDocument.objects.none()
    serializer_class = CommunityDocumentSerializer

    def get_queryset(self):
        if is_internal(self.request):
            qs = CommunityDocument.objects.all().order_by("id")
            return qs
        return CommunityDocument.objects.none()

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def discard(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.visible = False
        instance.save(version_user=request.user)
        instance.community.log_user_action(
            CommunityUserAction.ACTION_DISCARD_DOCUMENT.format(
                instance.document_number, instance.community.community_number
            ),
            request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.visible = True
        instance.save(version_user=request.user)
        instance.community.log_user_action(
            CommunityUserAction.ACTION_REINSTATE_DOCUMENT.format(
                instance.document_number, instance.community.community_number
            ),
            request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SaveCommunityDocumentSerializer(
            instance, data=json.loads(request.data.get("data"))
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(no_revision=True)
        instance.add_documents(request, version_user=request.user)
        instance.community.log_user_action(
            CommunityUserAction.ACTION_UPDATE_DOCUMENT.format(
                instance.document_number, instance.community.community_number
            ),
            request,
        )
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = SaveCommunityDocumentSerializer(
            data=json.loads(request.data.get("data"))
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            no_revision=True
        )  # only conduct revisions when documents have been added
        instance.add_documents(request, version_user=request.user)
        instance.community.log_user_action(
            CommunityUserAction.ACTION_ADD_DOCUMENT.format(
                instance.document_number, instance.community.community_number
            ),
            request,
        )
        return Response(serializer.data)


class ConservationThreatFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):

        total_count = queryset.count()

        filter_threat_category = request.GET.get("filter_threat_category")
        if filter_threat_category and not filter_threat_category.lower() == "all":
            queryset = queryset.filter(threat_category_id=filter_threat_category)

        filter_threat_current_impact = request.GET.get("filter_threat_current_impact")
        if (
            filter_threat_current_impact
            and not filter_threat_current_impact.lower() == "all"
        ):
            queryset = queryset.filter(current_impact=filter_threat_current_impact)

        filter_threat_potential_impact = request.GET.get(
            "filter_threat_potential_impact"
        )
        if (
            filter_threat_potential_impact
            and not filter_threat_potential_impact.lower() == "all"
        ):
            queryset = queryset.filter(potential_impact=filter_threat_potential_impact)

        filter_threat_status = request.GET.get("filter_threat_status")
        if filter_threat_status and not filter_threat_status.lower() == "all":
            if filter_threat_status == "active":
                queryset = queryset.filter(visible=True)
            elif filter_threat_status == "removed":
                queryset = queryset.filter(visible=False)

        def get_date(filter_date):
            date = request.GET.get(filter_date)
            if date:
                date = datetime.strptime(date, "%Y-%m-%d")
            return date

        filter_observed_from_date = get_date("filter_observed_from_date")
        if filter_observed_from_date:
            queryset = queryset.filter(date_observed__gte=filter_observed_from_date)

        filter_observed_to_date = get_date("filter_observed_to_date")
        if filter_observed_to_date:
            queryset = queryset.filter(date_observed__lte=filter_observed_to_date)

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, "_datatables_total_count", total_count)
        return queryset


class ConservationThreatViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = ConservationThreat.objects.none()
    serializer_class = ConservationThreatSerializer
    filter_backends = (ConservationThreatFilterBackend,)

    def get_queryset(self):
        if is_internal(self.request):
            qs = ConservationThreat.objects.all().order_by("id")
            return qs
        else:
            qs = (
                ConservationThreat.objects.filter(visible=True)
                .filter(
                    (
                        Q(species__species_publishing_status__species_public=True)
                        & Q(species__species_publishing_status__threats_public=True)
                    )
                    | (
                        Q(community__community_publishing_status__community_public=True)
                        & Q(community__community_publishing_status__threats_public=True)
                    )
                )
                .order_by("id")
            )
            return qs

    def update_publishing_status(self):

        # if the parent species or community of this threat is public
        # AND the threat section has been made public
        # revert back to private on any change
        instance = self.get_object()
        if instance.species:
            publishing_status_instance, created = (
                SpeciesPublishingStatus.objects.get_or_create(species=instance.species)
            )
            if publishing_status_instance.threats_public:
                publishing_status_instance.species_public = False
                publishing_status_instance.save()
        elif instance.community:
            publishing_status_instance, created = (
                CommunityPublishingStatus.objects.get_or_create(
                    community=instance.community
                )
            )
            if publishing_status_instance.threats_public:
                publishing_status_instance.community_public = False
                publishing_status_instance.save()

    # used for Threat Form dropdown lists
    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def threat_list_of_values(self, request, *args, **kwargs):
        """Used by the internal threat form"""
        threat_category_lists = []
        threat_categories = ThreatCategory.objects.all()
        if threat_categories:
            for choice in threat_categories:
                threat_category_lists.append(
                    {
                        "id": choice.id,
                        "name": choice.name,
                    }
                )

        current_impact_lists = []
        current_impacts = CurrentImpact.objects.all()
        if current_impacts:
            for choice in current_impacts:
                current_impact_lists.append(
                    {
                        "id": choice.id,
                        "name": choice.name,
                    }
                )
        potential_impact_lists = []
        potential_impacts = PotentialImpact.objects.all()
        if current_impacts:
            for choice in potential_impacts:
                potential_impact_lists.append(
                    {
                        "id": choice.id,
                        "name": choice.name,
                    }
                )
        potential_threat_onset_lists = []
        potential_threats = PotentialThreatOnset.objects.all()
        if potential_threats:
            for choice in potential_threats:
                potential_threat_onset_lists.append(
                    {
                        "id": choice.id,
                        "name": choice.name,
                    }
                )
        threat_agent_lists = []
        threat_agents = ThreatAgent.objects.all()
        if threat_agents:
            for choice in threat_agents:
                threat_agent_lists.append(
                    {
                        "id": choice.id,
                        "name": choice.name,
                    }
                )
        res_json = {
            "threat_category_lists": threat_category_lists,
            "current_impact_lists": current_impact_lists,
            "potential_impact_lists": potential_impact_lists,
            "potential_threat_onset_lists": potential_threat_onset_lists,
            "threat_agent_lists": threat_agent_lists,
        }
        res_json = json.dumps(res_json)
        return HttpResponse(res_json, content_type="application/json")

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def discard(self, request, *args, **kwargs):
        if not is_internal(self.request):  # TODO group checks
            raise serializers.ValidationError("user not authorised to discard threat")
        instance = self.get_object()
        instance.visible = False
        instance.save(version_user=request.user)
        if instance.species:
            instance.species.log_user_action(
                SpeciesUserAction.ACTION_DISCARD_THREAT.format(
                    instance.threat_number, instance.species.species_number
                ),
                request,
            )
        elif instance.community:
            instance.community.log_user_action(
                CommunityUserAction.ACTION_DISCARD_THREAT.format(
                    instance.threat_number, instance.community.community_number
                ),
                request,
            )

        self.update_publishing_status()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    def reinstate(self, request, *args, **kwargs):
        if not is_internal(self.request):  # TODO group checks
            raise serializers.ValidationError("user not authorised to reinstate threat")
        instance = self.get_object()
        instance.visible = True
        instance.save(version_user=request.user)
        if instance.species:
            instance.species.log_user_action(
                SpeciesUserAction.ACTION_REINSTATE_THREAT.format(
                    instance.threat_number, instance.species.species_number
                ),
                request,
            )
        elif instance.community:
            instance.community.log_user_action(
                CommunityUserAction.ACTION_REINSTATE_THREAT.format(
                    instance.threat_number, instance.community.community_number
                ),
                request,
            )

        self.update_publishing_status()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if not is_internal(self.request):  # TODO group checks
            raise serializers.ValidationError("user not authorised to update threat")
        instance = self.get_object()
        serializer = SaveConservationThreatSerializer(
            instance, data=json.loads(request.data.get("data"))
        )
        validate_threat_request(request)
        serializer.is_valid(raise_exception=True)
        serializer.save(version_user=request.user)
        if instance.species:
            instance.species.log_user_action(
                SpeciesUserAction.ACTION_UPDATE_THREAT.format(
                    instance.threat_number, instance.species.species_number
                ),
                request,
            )
        elif instance.community:
            instance.community.log_user_action(
                CommunityUserAction.ACTION_UPDATE_THREAT.format(
                    instance.threat_number, instance.community.community_number
                ),
                request,
            )

        self.update_publishing_status()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not is_internal(self.request):  # TODO group checks
            raise serializers.ValidationError("user not authorised to create threat")
        serializer = SaveConservationThreatSerializer(
            data=json.loads(request.data.get("data"))
        )
        validate_threat_request(request)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(version_user=request.user)
        if instance.species:
            instance.species.log_user_action(
                SpeciesUserAction.ACTION_ADD_THREAT.format(
                    instance.threat_number, instance.species.species_number
                ),
                request,
            )
            publishing_status_instance, created = (
                SpeciesPublishingStatus.objects.get_or_create(species=instance.species)
            )
            if publishing_status_instance.threats_public:
                publishing_status_instance.species_public = False
                publishing_status_instance.save()
        elif instance.community:
            instance.community.log_user_action(
                CommunityUserAction.ACTION_ADD_THREAT.format(
                    instance.threat_number, instance.community.community_number
                ),
                request,
            )
            publishing_status_instance, created = (
                CommunityPublishingStatus.objects.get_or_create(
                    community=instance.community
                )
            )
            if publishing_status_instance.threats_public:
                publishing_status_instance.community_public = False
                publishing_status_instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all().order_by("id")
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.order_by("id")
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
