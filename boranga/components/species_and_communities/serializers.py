import logging

from django.conf import settings
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from boranga.components.species_and_communities.models import(
	GroupType,
	Species,
	SpeciesLogEntry,
	Community,
	Taxonomy,
	TaxonVernacular,
	InformalGroup,
	ClassificationSystem,
	CommunityTaxonomy,
	SpeciesConservationAttributes,
	CommunityConservationAttributes,
	SpeciesDocument,
	CommunityDocument,
	SpeciesDistribution,
	CommunityDistribution,
	ConservationThreat,
	CommunityLogEntry,
	CommunityUserAction,
	SpeciesUserAction,
	)
from boranga.components.conservation_status.models import(
    ConservationStatus,
    )
from boranga.components.conservation_status.serializers import(
    SpeciesConservationStatusSerializer,
    CommunityConservationStatusSerializer,
    )

from boranga.components.users.serializers import UserSerializer
from boranga.components.users.serializers import UserAddressSerializer, DocumentSerializer
from boranga.components.main.serializers import CommunicationLogEntrySerializer, EmailUserSerializer
from boranga.ledger_api_utils import retrieve_email_user
from rest_framework import serializers
from django.db.models import Q

logger = logging.getLogger('boranga')

class ListSpeciesSerializer(serializers.ModelSerializer):
	group_type = serializers.SerializerMethodField()
	scientific_name = serializers.SerializerMethodField()
	common_name = serializers.SerializerMethodField()
	family = serializers.SerializerMethodField()
	genus = serializers.SerializerMethodField()
	phylogenetic_group = serializers.SerializerMethodField()
	conservation_list = serializers.SerializerMethodField()
	conservation_category = serializers.SerializerMethodField()
	region = serializers.SerializerMethodField()
	district = serializers.SerializerMethodField()
	processing_status = serializers.CharField(source='get_processing_status_display')
	user_process = serializers.SerializerMethodField(read_only=True)

	class Meta:
		model = Species
		fields = (
			    'id',
			    'species_number',
			    'group_type',
			    'scientific_name',
			    'common_name',
			    'family',
			    'genus',
			    'phylogenetic_group',
			    'region',
			    'district',
			    'conservation_list',
			    'conservation_category',
			    'processing_status',
				'can_user_edit',
				'can_user_view',
				'user_process',
				'comment',
			)
		datatables_always_serialize = (
                'id',
                'species_number',
                'group_type',
			    'scientific_name',
			    'common_name',
			    'family',
			    'genus',
			    'phylogenetic_group',
			    'region',
			    'district',
			    'conservation_list',
			    'conservation_category',
			    'processing_status',
				'can_user_edit',
				'can_user_view',
				'user_process',
				'comment'
			)	

	def get_group_type(self,obj):
		return obj.group_type.name

	def get_scientific_name(self,obj):
		if obj.taxonomy:
			return obj.taxonomy.scientific_name
		return ''
	
	def get_common_name(self,obj):
		if obj.taxonomy:
			if obj.taxonomy.vernaculars:
				names_list=obj.taxonomy.vernaculars.all().values_list('vernacular_name', flat=True)
				return ','.join(names_list)
		return ''

	def get_family(self,obj):
		if obj.taxonomy:
			if obj.taxonomy.family_fk:
				return obj.taxonomy.family_fk.scientific_name
		return ''

	def get_genus(self,obj):
		if obj.taxonomy:
			if obj.taxonomy.genus:
				return obj.taxonomy.genus.name
		return ''

	def get_phylogenetic_group(self,obj):
		if obj.taxonomy:
			if obj.taxonomy.informal_groups:
				return obj.taxonomy.informal_groups.all().values_list('classification_system_fk_id__class_desc', flat=True)
		return ''

	def get_conservation_list(self,obj):
		try:
			# need to show only WA_listed species
			conservation_status = ConservationStatus.objects.get(
				species=obj ,
				conservation_list__applies_to_wa=True,
				processing_status='approved'
			) # need to show only WA_list species
			return conservation_status.conservation_list.code
		except ConservationStatus.DoesNotExist:
			return ''

	def get_conservation_category(self,obj):
		try:
			# need to show only WA_list species
			conservation_status = ConservationStatus.objects.get(
				species=obj ,
				conservation_list__applies_to_wa=True,
				processing_status='approved'
			) # need to show only WA_list species
			return conservation_status.conservation_category.code
		except ConservationStatus.DoesNotExist:
			return ''

	def get_region(self,obj):
		if obj.region:
			return obj.region.name
		return ''

	def get_district(self,obj):
		if obj.district:
			return obj.district.name
		return ''

	def get_user_process(self,obj):
        # Check if currently logged in user has access to process the Species
		request = self.context['request']
		template_group = self.context.get('template_group')
		user = request.user
		if obj.can_user_action:
			#TODO user should be SystemGroup SpeciesProcessGroup?
			if user in obj.allowed_species_processors:
				return True
		return False

class ListCommunitiesSerializer(serializers.ModelSerializer):
	group_type = serializers.SerializerMethodField()
	#conservation_status = serializers.SerializerMethodField()
	community_migrated_id = serializers.SerializerMethodField()
	community_name = serializers.SerializerMethodField()
	conservation_list = serializers.SerializerMethodField()
	conservation_category = serializers.SerializerMethodField()
	region = serializers.SerializerMethodField()
	district = serializers.SerializerMethodField()
	processing_status = serializers.CharField(source='get_processing_status_display')
	user_process = serializers.SerializerMethodField(read_only=True)
	class Meta:
		model = Community
		fields = (
			    'id',
			    'community_number',
			    'group_type',
			    'community_migrated_id',
			    'community_name',
			    #'conservation_status',
			    'conservation_list',
			    'conservation_category',
			    'region',
			    'district',
				'processing_status',
				'can_user_edit',
				'can_user_view',
				'user_process',
				'comment'
			)
		datatables_always_serialize = (
                'id',
                'community_number',
                'group_type',
			    'community_migrated_id',
			    'community_name',
			    #'conservation_status',
			    'conservation_list',
			    'conservation_category',
			    'region',
			    'district',
				'processing_status',
				'can_user_edit',
				'can_user_view',
				'user_process',
				'comment'
			)

	def get_group_type(self,obj):
		return obj.group_type.name

	# def get_conservation_status(self,obj):
	# 	try:
	# 		conservation_status = CommunityConservationStatus.objects.get(community=obj)
	# 		return conservation_status.conservation_list.code
	# 	except CommunityConservationStatus.DoesNotExist:
	# 		return None

	def get_community_name(self,obj):
		try:
			taxonomy = CommunityTaxonomy.objects.get(community=obj)
			return taxonomy.community_name
		except CommunityTaxonomy.DoesNotExist:
			return ''
	
	def get_community_migrated_id(self,obj):
		try:
			taxonomy = CommunityTaxonomy.objects.get(community=obj)
			return taxonomy.community_migrated_id
		except CommunityTaxonomy.DoesNotExist:
			return ''

	def get_conservation_list(self,obj):
		try:
			#conservation_status = ConservationStatus.objects.get(community=obj,conservation_list__applies_to_wa=True) # TODO need to show only WA_list species
			conservation_status = ConservationStatus.objects.get(
				community=obj ,
				conservation_list__applies_to_wa=True,
				processing_status='approved'
			) # need to show only WA_list species
			return conservation_status.conservation_list.code
		except ConservationStatus.DoesNotExist:
			return ''

	def get_conservation_category(self,obj):
		try:
			#conservation_status = ConservationStatus.objects.get(community=obj,conservation_list__applies_to_wa=True)
			conservation_status = ConservationStatus.objects.get(
				community=obj ,
				conservation_list__applies_to_wa=True,
				processing_status='approved'
			) # need to show only WA_list species
			return conservation_status.conservation_category.code
		except ConservationStatus.DoesNotExist:
			return ''

	def get_region(self,obj):
		if obj.region:
			return obj.region.name
		return ''

	def get_district(self,obj):
		if obj.district:
			return obj.district.name
		return ''
	
	def get_user_process(self,obj):
        # Check if currently logged in user has access to process the Species
		request = self.context['request']
		template_group = self.context.get('template_group')
		user = request.user
		if obj.can_user_action:
			#TODO user should be SystemGroup SpeciesProcessGroup?
			if user in obj.allowed_community_processors:
				return True
		return False


class TaxonomySerializer(serializers.ModelSerializer):
	# text is added as need for select2 format
	text = serializers.SerializerMethodField()
	common_name = serializers.SerializerMethodField()
	phylogenetic_group = serializers.SerializerMethodField()
	class Meta:
		model = Taxonomy
		fields = (
			'id',
			'text',
			'taxon_name_id',
			'scientific_name',
			'kingdom_name',
			# need to fetch common name in multiple select
			'common_name',
			'taxon_previous_name',
			'family_fk_id',
			'genus_id',
			'phylogenetic_group',
			'name_authority',
			'name_comments',
			)
		
	def get_text(self,obj):
		return obj.scientific_name

	def get_common_name(self,obj):
		try:
			if obj.vernaculars:
				names_list = obj.vernaculars.all().values_list('vernacular_name', flat=True)
				return ','.join(names_list)
		except TaxonVernacular.DoesNotExist:
			return ''

	def get_phylogenetic_group(self,obj):
		try:
			if obj.informal_groups:
				# informal_groups = InformalGroup.objects.get(taxonomy=obj.id)
				informal_groups = InformalGroup.objects.filter(taxonomy_id=obj.id).values_list('classification_system_fk__class_desc', flat=True)
				return ','.join(informal_groups)
		except InformalGroup.DoesNotExist:
			return ''

class SpeciesConservationAttributesSerializer(serializers.ModelSerializer):

	class Meta:
		model = SpeciesConservationAttributes
		fields = (
			'id',
			'species_id',
			#flora related attributes
			'flowering_period',
			'fruiting_period',
			'flora_recruitment_type_id',
			'flora_recruitment_notes',
			'seed_viability_germination_info',
			'root_morphology_id',
			'pollinator_information',
			'hydrology',
			'response_to_dieback',
			# fauna related attributes
			'breeding_period',
			'fauna_breeding',
			'fauna_reproductive_capacity',
			'diet_and_food_source',
			'home_range',
			# common attributes
			'habitat_growth_form',
			'time_to_maturity_from',
			'time_to_maturity_to',
			'time_to_maturity_choice',
			'generation_length_from',
			'generation_length_to',
			'generation_length_choice',
			'average_lifespan_from',
			'average_lifespan_to',
			'average_lifespan_choice',
			'minimum_fire_interval_from',
    		'minimum_fire_interval_to',
    		'minimum_fire_interval_choice',
			'response_to_fire',
			'post_fire_habitat_interaction_id',
			'response_to_disturbance',
			'habitat',
			'research_requirements',
			'other_relevant_diseases',
			)
		
		def __init__(self, *args, **kwargs):
			super(SpeciesConservationAttributesSerializer, self).__init__(*args, **kwargs)
			PERIOD_CHOICES = []
			for rs in SpeciesConservationAttributes.PERIOD_CHOICES:
				PERIOD_CHOICES.append(([rs[0], rs[1]]))
			self.fields['flowering_period', 'fruiting_period', 'breeding_period'] = serializers.MultipleChoiceField(choices=PERIOD_CHOICES, allow_blank=False)


class SaveSpeciesConservationAttributesSerializer(serializers.ModelSerializer):
	species_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	flowering_period = serializers.MultipleChoiceField(choices=SpeciesConservationAttributes.PERIOD_CHOICES, allow_null=True, allow_blank=True, required=False)
	fruiting_period = serializers.MultipleChoiceField(choices=SpeciesConservationAttributes.PERIOD_CHOICES, allow_null=True, allow_blank=True, required=False)
	flora_recruitment_type_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	root_morphology_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	breeding_period = serializers.MultipleChoiceField(choices=SpeciesConservationAttributes.PERIOD_CHOICES, allow_null=True, allow_blank=True, required=False)
	post_fire_habitat_interaction_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = SpeciesConservationAttributes
		fields = (
			'id',
			'species_id',
			#flora related attributes
			'flowering_period',
			'fruiting_period',
			'flora_recruitment_type_id',
			'flora_recruitment_notes',
			'seed_viability_germination_info',
			'root_morphology_id',
			'pollinator_information',
			'hydrology',
			'response_to_dieback',
			# fauna related attributes
			'breeding_period',
			'fauna_breeding',
			'fauna_reproductive_capacity',
			'diet_and_food_source',
			'home_range',
			# common attributes
			'habitat_growth_form',
			'time_to_maturity_from',
			'time_to_maturity_to',
			'time_to_maturity_choice',
			'generation_length_from',
			'generation_length_to',
			'generation_length_choice',
			'average_lifespan_from',
			'average_lifespan_to',
			'average_lifespan_choice',
			'minimum_fire_interval_from',
    		'minimum_fire_interval_to',
    		'minimum_fire_interval_choice',
			'response_to_fire',
			'post_fire_habitat_interaction_id',
			'response_to_disturbance',
			'habitat',
			'research_requirements',
			'other_relevant_diseases',
			)


class SpeciesDistributionSerializer(serializers.ModelSerializer):
	cal_number_of_occurrences = serializers.SerializerMethodField() # calculated from occurence reports
	cal_extent_of_occurrences = serializers.SerializerMethodField() # calculated from occurence reports
	cal_area_of_occupancy = serializers.SerializerMethodField() # calculated from occurence reports
	cal_area_of_occupancy_actual = serializers.SerializerMethodField() # calculated from occurence reports
	class Meta:
		model = SpeciesDistribution
		fields = (
			'department_file_numbers',
			'number_of_occurrences',
			'cal_number_of_occurrences',
			'noo_auto',
			'extent_of_occurrences',
			'cal_extent_of_occurrences',
			'eoo_auto',
			'area_of_occupancy',
			'cal_area_of_occupancy',
			'aoo_auto',
			'area_of_occupancy_actual',
			'cal_area_of_occupancy_actual',
			'aoo_actual_auto',
			'number_of_iucn_locations',
			'number_of_iucn_subpopulations'
			)

	def get_cal_number_of_occurrences(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_extent_of_occurrences(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_area_of_occupancy(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_area_of_occupancy_actual(self,obj):
		return 1 # TODO get calculated value from occurrence report


class SaveSpeciesDistributionSerializer(serializers.ModelSerializer):
	species_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = SpeciesDistribution
		fields = (
			'species_id',
			'department_file_numbers',
			'number_of_occurrences',
			'noo_auto',
			'extent_of_occurrences',
			'eoo_auto',
			'area_of_occupancy',
			'aoo_auto',
			'area_of_occupancy_actual',
			'aoo_actual_auto',
			'number_of_iucn_locations',
			'number_of_iucn_subpopulations'
			)


class BaseSpeciesSerializer(serializers.ModelSerializer):
	readonly = serializers.SerializerMethodField(read_only=True)
	group_type = serializers.SerializerMethodField(read_only=True)
	conservation_status = serializers.SerializerMethodField()
	taxonomy_details = serializers.SerializerMethodField()
	conservation_attributes = serializers.SerializerMethodField()
	distribution = serializers.SerializerMethodField()
	image_doc=serializers.SerializerMethodField()
	allowed_species_processors = EmailUserSerializer(many=True)
	
	class Meta:
		model = Species
		fields = (
			'id',
			'species_number',
			'group_type',
			'group_type_id',
			'taxonomy_id',
			'conservation_status',
			'taxonomy_details',
			'conservation_attributes',
			'distribution',
			'region_id',
			'district_id',
			'last_data_curration_date',
			'image_doc'
			'processing_status',
			'applicant',
			'submitter',
			'lodgement_date',
			'readonly',
			'can_user_edit',
			'can_user_view',
			'applicant_details',
			'allowed_species_processors',
			'comment'
			)
			
	def get_readonly(self,obj):
		return False

	def get_group_type(self,obj):
		return obj.group_type.name

	# TODO not used on the form yet as gives error for new species as taxonomy = null 
	def get_taxonomy_details(self,obj):
		try:
			if obj.taxonomy:
				qs = obj.taxonomy
				return TaxonomySerializer(qs).data
		except Taxonomy.DoesNotExist:
			return TaxonomySerializer().data

	def get_conservation_status(self,obj):
		try:
			qs = ConservationStatus.objects.get(
        		species=obj ,
        		conservation_list__applies_to_wa=True,
        		processing_status='approved'
        	)
			return SpeciesConservationStatusSerializer(qs).data
		except ConservationStatus.DoesNotExist:
			return SpeciesConservationStatusSerializer().data
			#return [SpeciesConservationStatusSerializer(qs).data] # this array was used for dashboard on profile page
	
	def get_conservation_attributes(self,obj):
		try:
			qs = SpeciesConservationAttributes.objects.get(species=obj)
			return SpeciesConservationAttributesSerializer(qs).data
		except SpeciesConservationAttributes.DoesNotExist:
			return SpeciesConservationAttributesSerializer().data

	def get_distribution(self,obj):
		try:
    	    # to create the distribution instance for fetching the calculated values from serializer
			distribution_instance, created = SpeciesDistribution.objects.get_or_create(species=obj)
			return SpeciesDistributionSerializer(distribution_instance).data
		except SpeciesDistribution.DoesNotExist:
			return SpeciesDistributionSerializer().data

	def get_image_doc(self,obj):
		if obj.image_doc and obj.image_doc._file:
			return obj.image_doc._file.url
		return None

	def get_processing_status(self,obj):
		return obj.get_processing_status_display()


class SpeciesSerializer(BaseSpeciesSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    
    def get_readonly(self,obj):
        return obj.can_user_view

    # Priya updated as gives error for submitter when resubmit after amendment request
    def get_submitter(self,obj):
        # if obj.submitter:
        #     email_user = retrieve_email_user(obj.submitter)
        #     return email_user.get_full_name()
        # else:
        #     return None
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None


class InternalSpeciesSerializer(BaseSpeciesSerializer):
	submitter = serializers.SerializerMethodField(read_only=True)
	processing_status = serializers.SerializerMethodField(read_only=True)
	current_assessor = serializers.SerializerMethodField()
	allowed_species_processors = EmailUserSerializer(many=True)
	user_edit_mode = serializers.SerializerMethodField()
	reversion_ids = serializers.SerializerMethodField()

	class Meta:
		model = Species
		fields = (
			'id',
			'species_number',
			'group_type',
			'group_type_id',
			'taxonomy_id',
			'conservation_status',
			'taxonomy_details',
			'conservation_attributes',
			'distribution',
			'region_id',
			'district_id',
			'last_data_curration_date',
			'image_doc',
			'processing_status',
			'readonly',
			'can_user_edit',
			'can_user_view',
			'submitter',
			'lodgement_date',
			'current_assessor',
			'allowed_species_processors',
			'user_edit_mode',
			'comment',
			'reversion_ids',
			)

	def get_submitter(self, obj):
		if obj.submitter:
			email_user = retrieve_email_user(obj.submitter)
			return EmailUserSerializer(email_user).data
		else:
			return None

	def get_readonly(self,obj):
        # for internal add new conservation status change the below readonly
        #return True
        # Check if in 'draft' shouldn't be editable internal(if application is external) but should be editable(if internal_application)
		if obj.can_user_edit:
			return False
		else:
			return obj.can_user_view

	def get_current_assessor(self, obj):
		return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

	def get_user_edit_mode(self,obj):
		# TODO check if the proposal has been accepted or declined
		request = self.context["request"]
		user = (
			request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
		)
		return obj.has_user_edit_mode(user)
	
	def get_reversion_ids(self,obj):
		if hasattr(obj,"reversion_ids"):
			return obj.reversion_ids[:5]
		return


class CommunityDistributionSerializer(serializers.ModelSerializer): 
	cal_number_of_occurrences = serializers.SerializerMethodField() # calculated from occurence reports
	cal_extent_of_occurrences = serializers.SerializerMethodField() # calculated from occurence reports
	cal_area_of_occupancy = serializers.SerializerMethodField() # calculated from occurence reports
	cal_area_of_occupancy_actual = serializers.SerializerMethodField() # calculated from occurence reports

	class Meta:
		model = CommunityDistribution
		fields = (
			'department_file_numbers',
			'number_of_occurrences',
			'cal_number_of_occurrences',
			'noo_auto',
			'extent_of_occurrences',
			'cal_extent_of_occurrences',
			'eoo_auto',
			'area_of_occupancy',
			'cal_area_of_occupancy',
			'aoo_auto',
			'area_of_occupancy_actual',
			'cal_area_of_occupancy_actual',
			'aoo_actual_auto',
			'number_of_iucn_locations',
			'number_of_iucn_subpopulations',
			'community_original_area',
			'community_original_area_accuracy',
			'community_original_area_reference',
			)

	def get_cal_number_of_occurrences(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_extent_of_occurrences(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_area_of_occupancy(self,obj):
		return 1 # TODO get calculated value from occurrence report

	def get_cal_area_of_occupancy_actual(self,obj):
		return 1 # TODO get calculated value from occurrence report


class SaveCommunityDistributionSerializer(serializers.ModelSerializer): 
	community_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = CommunityDistribution
		fields = (
			'community_id',
			'department_file_numbers',
			'number_of_occurrences',
			'noo_auto',
			'extent_of_occurrences',
			'eoo_auto',
			'area_of_occupancy',
			'aoo_auto',
			'area_of_occupancy_actual',
			'aoo_actual_auto',
			'number_of_iucn_locations',
			'number_of_iucn_subpopulations',
			'community_original_area',
			'community_original_area_accuracy',
			'community_original_area_reference',
			)


class SpeciesSerializer(serializers.ModelSerializer):
	scientific_name = serializers.SerializerMethodField()
	class Meta:
		model = Species
		fields = (
			'id',
			'scientific_name',
			)

	def get_scientific_name(self,obj):
		if obj.taxonomy:
			return obj.taxonomy.scientific_name
		return ''


class CommunityConservationAttributesSerializer(serializers.ModelSerializer):
	class Meta:
		model = CommunityConservationAttributes
		fields = (
			'id',
			'community_id',
			# 'habitat_growth_form',
			'pollinator_information',
			'minimum_fire_interval_from',
    		'minimum_fire_interval_to',
    		'minimum_fire_interval_choice',
			'response_to_fire',
			'post_fire_habitat_interaction_id',
			'hydrology',
			'ecological_and_biological_information',
			'research_requirements',
			'response_to_dieback',
			'other_relevant_diseases',
			)


class SaveCommunityConservationAttributesSerializer(serializers.ModelSerializer):
	community_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	post_fire_habitat_interaction_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = CommunityConservationAttributes
		fields = (
			'id',
			'community_id',
			# 'habitat_growth_form',
			'pollinator_information',
			'minimum_fire_interval_from',
    		'minimum_fire_interval_to',
    		'minimum_fire_interval_choice',
			'response_to_fire',
			'post_fire_habitat_interaction_id',
			'hydrology',
			'ecological_and_biological_information',
			'research_requirements',
			'response_to_dieback',
			'other_relevant_diseases',
			)

class CommunityTaxonomySerializer(serializers.ModelSerializer):
	text = serializers.SerializerMethodField()
	
	class Meta:
		model = CommunityTaxonomy
		fields = (
			'id',
			'text',
			'community_id',
			'community_migrated_id',
			'community_name',
			'community_description',
			'previous_name',
			'name_authority',
			'name_comments',
			)

	def get_text(self,obj):
		return obj.community_name


class SaveCommunityTaxonomySerializer(serializers.ModelSerializer):
	community_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = CommunityTaxonomy
		fields = (
			'id',
			'community_id',
			'community_migrated_id',
			'community_name',
			'community_description',
			'previous_name',
			'name_authority',
			'name_comments',
			)


class BaseCommunitySerializer(serializers.ModelSerializer):
	species = serializers.SerializerMethodField()
	group_type = serializers.SerializerMethodField(read_only=True)
	taxonomy_details = serializers.SerializerMethodField()
	conservation_status = serializers.SerializerMethodField()
	distribution = serializers.SerializerMethodField()
	conservation_attributes = serializers.SerializerMethodField()
	readonly = serializers.SerializerMethodField(read_only=True)
	image_doc = serializers.SerializerMethodField()
	allowed_community_processors = EmailUserSerializer(many=True)

	class Meta:
		model = Community
		fields = (
        	    'id',
        	    'community_number',
        	    'species',
			    'group_type',
				'taxonomy_details',
			    'region_id',
			    'district_id',
			    'conservation_status',
			    'distribution',
			    'conservation_attributes',
			    'last_data_curration_date',
				'image_doc',
				'processing_status',
				'lodgement_date',
				'submitter',
			    'readonly',
			    'can_user_edit',
				'can_user_view',
				'applicant_details',
				'allowed_community_processors',
				'comment'
				)

	def get_species(self,obj):
		return [s.id for s in obj.species.all()]
	
	def get_readonly(self,obj):
		return False

	def get_group_type(self,obj):
		return obj.group_type.name

	# TODO not used on the form yet as gives error for new species as taxonomy = null 
	def get_taxonomy_details(self,obj):
		try:
			taxonomy_instance, created = CommunityTaxonomy.objects.get_or_create(community=obj)
			return CommunityTaxonomySerializer(taxonomy_instance).data
		except:
			qs = None
		return CommunityTaxonomySerializer(qs).data

	def get_conservation_status(self,obj):
		try:
			qs = ConservationStatus.objects.get(
				community=obj ,
				conservation_list__applies_to_wa=True,
				processing_status='approved')
			return CommunityConservationStatusSerializer(qs).data
		except ConservationStatus.DoesNotExist:
			return CommunityConservationStatusSerializer().data
			#return [CommunityConservationStatusSerializer(qs).data] # this array was used for dashboard on profile page

	def get_distribution(self,obj):
		try:
		    # to create the distribution instance for fetching the calculated values from serializer
			distribution_instance, created = CommunityDistribution.objects.get_or_create(community=obj)
			return CommunityDistributionSerializer(distribution_instance).data
		except:
			qs = None
		return CommunityDistributionSerializer(qs).data

	def get_conservation_attributes(self,obj):
		try:
			qs = CommunityConservationAttributes.objects.get(community=obj)
			return CommunityConservationAttributesSerializer(qs).data
		except CommunityConservationAttributes.DoesNotExist:
			return CommunityConservationAttributesSerializer().data

	def get_can_user_edit(self,obj):
		return True

	def get_submitter(self, obj):
		if obj.submitter:
			email_user = retrieve_email_user(obj.submitter)
			#return email_user.get_full_name()
			return EmailUserSerializer(email_user).data

		else:
			return None

	def get_image_doc(self,obj):
		if obj.image_doc and obj.image_doc._file:
			return obj.image_doc._file.url
		return None

	def get_processing_status(self,obj):
		return obj.get_processing_status_display()


class CommunitySerializer(BaseCommunitySerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)

    def get_readonly(self,obj):
        return obj.can_user_view

    # Priya updated as gives error for submitter when resubmit after amendment request
    def get_submitter(self,obj):
        # if obj.submitter:
        #     email_user = retrieve_email_user(obj.submitter)
        #     return email_user.get_full_name()
        # else:
        #     return None
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None


class InternalCommunitySerializer(BaseCommunitySerializer):
	submitter = serializers.SerializerMethodField(read_only=True)
	processing_status = serializers.SerializerMethodField(read_only=True)
	current_assessor = serializers.SerializerMethodField()
	allowed_community_processors = EmailUserSerializer(many=True)
	user_edit_mode = serializers.SerializerMethodField()
	reversion_ids = serializers.SerializerMethodField()

	class Meta:
		model = Community
		fields = (
			'id',
			'community_number',
			# 'species',
			'group_type',
			'taxonomy_details',
			'region_id',
			'district_id',
			'conservation_status',
			'distribution',
			'conservation_attributes',
			'last_data_curration_date',
			'image_doc',
			'processing_status',
			'lodgement_date',
			'submitter',
			'readonly',
			'can_user_edit',
			'can_user_view',
			'current_assessor',
			'allowed_community_processors',
			'user_edit_mode',
			'comment',
			'reversion_ids',
			)

	def get_submitter(self, obj):
		if obj.submitter:
			email_user = retrieve_email_user(obj.submitter)
			return EmailUserSerializer(email_user).data
		else:
			return None

	def get_readonly(self,obj):
        # Check if in 'draft' shouldn't be editable internal(if application is external) but should be editable(if internal_application)
		if obj.can_user_edit:
			return False
		else:
			return obj.can_user_view

	def get_current_assessor(self, obj):
		return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

	def get_user_edit_mode(self,obj):
		# TODO check if the proposal has been accepted or declined
		request = self.context["request"]
		user = (
			request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
		)
		return obj.has_user_edit_mode(user)

	def get_reversion_ids(self,obj):
		if hasattr(obj,"reversion_ids"):
			return obj.reversion_ids[:5]
		return

class SaveSpeciesSerializer(BaseSpeciesSerializer):
    region_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
    district_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
    taxonomy_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
    class Meta:
        model = Species
        fields = ('id',
			    'group_type',
				'taxonomy_id',
			    'region_id',
			    'district_id',
			    'last_data_curration_date',
			    'submitter',
                'readonly',
                'can_user_edit',
                'can_user_view',
				'comment'
                )
        read_only_fields=('id','group_type')


class CreateSpeciesSerializer(BaseSpeciesSerializer):
	group_type_id = serializers.IntegerField(required=True, write_only= True)
	class Meta:
		model = Species
		fields = ('id',
			    'group_type_id',
				)
		read_only_fields = (
            'id',
            )


class SaveCommunitySerializer(BaseCommunitySerializer):
	region_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	district_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	
	class Meta:
		model = Community
		fields = ('id',
			    'group_type',
				'region_id',
			    'district_id',
			    'last_data_curration_date',
				'submitter',
			    'readonly',
			    'can_user_edit',
                'can_user_view',
				'comment'
			    )
		read_only_fields=('id','group_type')


class CreateCommunitySerializer(BaseCommunitySerializer):
    group_type_id = serializers.IntegerField(required=True, write_only= True)
    class Meta:
        model = Community
        fields = ('id',
			    'group_type_id',
			    )
        read_only_fields = (
            'id',
            )


class DocumentSerializer(serializers.ModelSerializer):
	class Meta:
		model = SpeciesDocument
		fields = ('id','name','_file')


class SpeciesDocumentSerializer(serializers.ModelSerializer):
	document_category_name = serializers.SerializerMethodField()
	document_sub_category_name = serializers.SerializerMethodField()
	class Meta:
		model = SpeciesDocument
		fields = (
			'id',
			'document_number',
			'species',
			'name',
			'_file',
			'description',
			'input_name',
			'uploaded_date',
			'document_category',
			'document_category_name',
			'document_sub_category',
			'document_sub_category_name',
			'visible',
		)
		read_only_fields = ('id','document_number')

	def get_document_category_name(self,obj):
		if obj.document_category:
			return obj.document_category.document_category_name

	def get_document_sub_category_name(self,obj):
		if obj.document_sub_category:
			return obj.document_sub_category.document_sub_category_name


class SaveSpeciesDocumentSerializer(serializers.ModelSerializer):
	class Meta:
		model = SpeciesDocument
		fields = (
			'id',
			'species',
			'name',
			'description',
			'input_name',
			'uploaded_date',
			'document_category',
			'document_sub_category',
			)


class CommunityDocumentSerializer(serializers.ModelSerializer):
	document_category_name = serializers.SerializerMethodField()
	document_sub_category_name = serializers.SerializerMethodField()
	class Meta:
		model = CommunityDocument
		fields = (
			'id',
			'document_number',
			'community',
			'name',
			'_file',
			'description',
			'input_name',
			'uploaded_date',
			'document_category',
			'document_category_name',
			'document_sub_category',
			'document_sub_category_name',
			'visible',
		)
		read_only_fields = ('id','document_number')

	def get_document_category_name(self,obj):
		if obj.document_category:
			return obj.document_category.document_category_name

	def get_document_sub_category_name(self,obj):
		if obj.document_sub_category:
			return obj.document_sub_category.document_sub_category_name


class SaveCommunityDocumentSerializer(serializers.ModelSerializer):
	class Meta:
		model = CommunityDocument
		fields = (
			'id',
			'community',
			'name',
			'description',
			'input_name',
			'uploaded_date',
			'document_category',
			'document_sub_category',
			)


class SpeciesLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = SpeciesLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

class SpeciesUserActionSerializer(serializers.ModelSerializer):
	who = serializers.SerializerMethodField()
	class Meta:
		model = SpeciesUserAction
		fields = '__all__'

	def get_who(self, species_user_action):
		email_user = retrieve_email_user(species_user_action.who)
		fullname = email_user.get_full_name()
		return fullname


class ConservationThreatSerializer(serializers.ModelSerializer):
	threat_category = serializers.SerializerMethodField()
	threat_agent = serializers.SerializerMethodField()
	current_impact_name = serializers.SerializerMethodField()
	potential_impact_name = serializers.SerializerMethodField()
	potential_threat_onset_name = serializers.SerializerMethodField()
	class Meta:
		model = ConservationThreat
		fields = (
			'id',
			'threat_number',
			'threat_category_id',
			'threat_category',
			'threat_agent',
			'threat_agent_id',
			'current_impact',
			'current_impact_name',
			'potential_impact',
			'potential_impact_name',
			'potential_threat_onset',
			'potential_threat_onset_name',
			'comment',
			'date_observed',
			'source',
			'species',
			'community',
			'visible',
		)
		read_only_fields = ('id','threat_number',)

	def get_threat_category(self,obj):
		if obj.threat_category:
			return obj.threat_category.name
	
	def get_threat_agent(self,obj):
		if obj.threat_agent:
			return obj.threat_agent.name

	def get_current_impact_name(self,obj):
		if obj.current_impact:
			return obj.current_impact.name

	def get_potential_impact_name(self,obj):
		if obj.potential_impact:
			return obj.potential_impact.name

	def get_potential_threat_onset_name(self,obj):
		if obj.potential_threat_onset:
			return obj.potential_threat_onset.name


class SaveConservationThreatSerializer(serializers.ModelSerializer):
	threat_category_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	threat_agent_id = serializers.IntegerField(required=False, allow_null=True, write_only= True)
	class Meta:
		model = ConservationThreat
		fields = (
			'id',
			'species',
			'community',
			'threat_category_id',
			'threat_agent_id',
			'comment',
			'current_impact',
			'potential_impact',
			'potential_threat_onset',
			'date_observed',
			)


class CommunityLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunityLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]


class CommunityUserActionSerializer(serializers.ModelSerializer):
	who = serializers.SerializerMethodField()
	class Meta:
		model = CommunityUserAction
		fields = '__all__'
	def get_who(self, community_user_action):
		email_user = retrieve_email_user(community_user_action.who)
		fullname = email_user.get_full_name()
		return fullname 

