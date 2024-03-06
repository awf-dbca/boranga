import datetime
import logging
import os
from django.db import models
from django.db.models import Q
from boranga.components.main.models import (
    CommunicationsLogEntry, 
    UserAction,
    Document
    )
import json
from django.core.cache import cache
import subprocess
from django.db import models,transaction
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from boranga.components.main.related_item import RelatedItem
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from boranga.ledger_api_utils import retrieve_email_user
from ledger_api_client.managed_models import SystemGroup
from multiselectfield import MultiSelectField
from reversion.models import Version
from boranga.settings import (
    GROUP_NAME_ASSESSOR,
    GROUP_NAME_APPROVER,
    GROUP_NAME_EDITOR,
    GROUP_NAME_SPECIES_COMMUNITIES_PROCESSOR,
)


logger = logging.getLogger(__name__)

private_storage = FileSystemStorage(location=settings.BASE_DIR+"/private-media/", base_url='/private-media/')

DISTRICT_PERTH_HILLS = 'PHS'
DISTRICT_SWAN_COASTAL = 'SWC'
DISTRICT_BLACKWOOD = 'BWD'
DISTRICT_WELLINGTON = 'WTN'
DISTRICT_DONNELLY = 'DON'
DISTRICT_FRANKLAND = 'FRK'
DISTRICT_ALBANY = 'ALB'
DISTRICT_ESPERANCE = 'ESP'
DISTRICT_EAST_KIMBERLEY = 'EKM'
DISTRICT_WEST_KIMBERLEY = 'WKM'
DISTRICT_EXMOUTH = 'EXM'
DISTRICT_PILBARA = 'PIL'
DISTRICT_KALGOORLIE = 'KAL'
DISTRICT_GERALDTON = 'GER'
DISTRICT_MOORA = 'MOR'
DISTRICT_SHARK_BAY = 'SHB'
DISTRICT_GREAT_SOUTHERN = 'GSN'
DISTRICT_CENTRAL_WHEATBELT = 'CWB'
DISTRICT_SOUTHERN_WHEATBELT = 'SWB'

DISTRICT_CHOICES = (
    (DISTRICT_PERTH_HILLS, "Perth Hills"),
    (DISTRICT_SWAN_COASTAL, "Swan Coastal"),
    (DISTRICT_BLACKWOOD, "Blackwood"),
    (DISTRICT_WELLINGTON, "Wellington"),
    (DISTRICT_DONNELLY, "Donnelly"),
    (DISTRICT_FRANKLAND, "Frankland"),
    (DISTRICT_ALBANY, "Albany"),
    (DISTRICT_ESPERANCE, "Esperance"),
    (DISTRICT_EAST_KIMBERLEY, "East Kimberley"),
    (DISTRICT_WEST_KIMBERLEY, "West Kimberley"),
    (DISTRICT_EXMOUTH, "Exmouth"),
    (DISTRICT_PILBARA, "Pilbara"),
    (DISTRICT_KALGOORLIE, "Kalgoorlie"),
    (DISTRICT_GERALDTON, "Geraldton"),
    (DISTRICT_MOORA, "Moora"),
    (DISTRICT_SHARK_BAY, "Shark Bay"),
    (DISTRICT_GREAT_SOUTHERN, "Great Southern"),
    (DISTRICT_CENTRAL_WHEATBELT, "Central Wheatbelt"),
    (DISTRICT_SOUTHERN_WHEATBELT, "Southern Wheatbelt")
)

REGION_KIMBERLEY = 'kimberley'
REGION_PILBARA = 'pilbara'
REGION_MIDWEST = 'midwest'
REGION_GOLDFIELDS = 'goldfields'
REGION_SWAN = 'swan'
REGION_WHEATBELT = 'wheatbelt'
REGION_SOUTH_WEST = 'southwest'
REGION_WARREN = 'warren'
REGION_SOUTH_COAST = 'southcoast'

REGION_CHOICES = (
    (REGION_KIMBERLEY,'Kimberley'),
    (REGION_PILBARA,'Pilbara'),
    (REGION_MIDWEST,'Midwest'),
    (REGION_GOLDFIELDS,'Goldfields'),
    (REGION_SWAN,'Swan'),
    (REGION_WHEATBELT,'Wheatbelt'),
    (REGION_SOUTH_WEST,'South West'),
    (REGION_WARREN,'Warren'),
    (REGION_SOUTH_COAST,'South Coast')
)

def update_species_doc_filename(instance, filename):
    return '{}/species/{}/species_documents/{}'.format(settings.MEDIA_APP_DIR, instance.species.id,filename)

def update_community_doc_filename(instance, filename):
    return '{}/community/{}/community_documents/{}'.format(settings.MEDIA_APP_DIR, instance.community.id,filename)

def update_species_comms_log_filename(instance, filename):
    return '{}/species/{}/communications/{}'.format(settings.MEDIA_APP_DIR, instance.log_entry.species.id,filename)

def update_community_comms_log_filename(instance, filename):
    return '{}/community/{}/communications/{}'.format(settings.MEDIA_APP_DIR, instance.log_entry.community.id,filename)


class Region(models.Model):
    name = models.CharField(choices=REGION_CHOICES, 
                            unique=True,
                            default=None,
                            max_length=64)

    class Meta:
        app_label = 'boranga'
        ordering = ['name']
        
    def __str__(self):
        return self.get_name_display()


class District(models.Model):
    name = models.CharField(choices=DISTRICT_CHOICES, 
                            unique=True,
                            max_length=64)
    region = models.ForeignKey(Region, 
                               on_delete=models.CASCADE )

    class Meta:
        app_label = 'boranga'
        ordering = ['name']
    def __str__(self):
        return self.get_name_display()


class GroupType(models.Model):
    """
    The three types of group managed by Boranga: fauna, flora and communities. These are the basis
    for all other models in Species and Communities.

    Has a:
    - N/A
    Used by:
    - Species
    - Community
    Is:
    - Enumeration (GroupTypes)
    """
    GROUP_TYPE_FLORA = 'flora'
    GROUP_TYPE_FAUNA = 'fauna'
    GROUP_TYPE_COMMUNITY = 'community'
    GROUP_TYPES = [(GROUP_TYPE_FLORA, 'Flora'), (GROUP_TYPE_FAUNA, 'Fauna'), (GROUP_TYPE_COMMUNITY, 'Community')]
    name = models.CharField(max_length=64,
                            choices=GROUP_TYPES,
                            default=GROUP_TYPES[1],)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Group Type"
        verbose_name_plural = "Group Types"

    def __str__(self):
        return self.get_name_display()

    @property
    def flora_kingdoms(self):
        return Kingdom.objects.get(grouptype__name=GroupType.GROUP_TYPE_FLORA).value_list('kingdom_name', flat=True)

    @property
    def fauna_kingdoms(self):
        return Kingdom.objects.get(grouptype__name=GroupType.GROUP_TYPE_FAUNA).value_list('kingdom_name', flat=True)


class Kingdom(models.Model):
    """
    create GroupType related Kingdoms matching the NOMOS api kingdom name 
    """
    grouptype = models.ForeignKey(GroupType,on_delete = models.CASCADE, null=True, blank=True, related_name='kingdoms')
    kingdom_id = models.CharField(max_length=100, null=True, blank=True)  # nomos data
    kingdom_name = models.CharField(max_length=100, null=True, blank=True) # nomos data

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return self.kingdom_name


class Genus(models.Model):
    """
    # list derived from WACensus

    Used by:
    - Taxonomy

    """
    name = models.CharField(max_length=200, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Genus"
        verbose_name_plural = "Genera"
        ordering = ['name']

    def __str__(self):
        return str(self.name)


class TaxonomyRank(models.Model):
    """
    Description from wacensus, to get the Kingdomwise taxon rank for particular taxon_name_id

    Used by:
    - Taxonomy
    Is:
    - Table
    """
    kingdom_id = models.IntegerField(null=True, blank=True)  # nomos data
    kingdom_fk = models.ForeignKey(Kingdom, on_delete=models.SET_NULL, null=True, blank=True, related_name="ranks")
    taxon_rank_id = models.IntegerField(null=True, blank=True)  # nomos data
    rank_name = models.CharField(max_length=512,null=True, blank=True)

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.rank_name)  # TODO: is the most appropriate?


class Taxonomy(models.Model):
    """
    Description from wacensus, to get the main name then fill in everything else

    Has a:
    Used by:
    - Species
    Is:
    - Table
    """
    taxon_name_id = models.IntegerField(null=True, blank=True)
    scientific_name = models.CharField(max_length=512,null=True, blank=True)
    kingdom_id = models.CharField(max_length=100,null=True, blank=True)
    kingdom_fk = models.ForeignKey(Kingdom, on_delete=models.SET_NULL, null=True, blank=True, related_name="taxons")
    kingdom_name = models.CharField(max_length=512,null=True, blank=True)
    taxon_rank_id = models.IntegerField(null=True, blank=True)
    taxonomy_rank_fk = models.ForeignKey(TaxonomyRank, on_delete=models.SET_NULL, null=True, blank=True, related_name="taxons")
    family_nid = models.IntegerField(null=True, blank=True)
    family_fk = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="taxon_family")
    genus = models.ForeignKey(Genus, on_delete=models.SET_NULL, null=True, blank=True)
    # phylogenetic_group is only used for Fauna 
    name_currency = models.CharField(max_length=16, null=True, blank=True) # is it the current name? yes or no
    previous_name = models.CharField(max_length=512,null=True, blank=True) # TODO this field is not used anymore
    name_authority = models.CharField(max_length=500,null=True, blank=True)
    name_comments = models.CharField(max_length=500,null=True, blank=True)
    path = models.CharField(max_length=512,null=True, blank=True) # hierarchy for given taxon

    class Meta:
        app_label = 'boranga'
        ordering = ['scientific_name']

    def __str__(self):
        return str(self.scientific_name)  # TODO: is the most appropriate?
    
    def save(self, *args, **kwargs):
        cache.delete('get_taxonomy_data')
        self.full_clean()
        super(Taxonomy, self).save(*args,**kwargs)

    @property
    def taxon_previous_name(self):
        if self.new_taxon.all():
            # cross_ref = CrossReference.objects.get(new_taxonomy_id=self.id)
            # return cross_ref.old_taxonomy.scientific_name
            # if taxon has more than one previous names
            # previous_names_list=self.new_taxon.all().values_list('old_taxonomy__scientific_name', flat=True)
            # commented the above as gives None scientific_name if there is no old_taxon instance in Taxonomy api data
            previous_names_list = CrossReference.objects.filter(~Q(old_taxonomy__scientific_name=None), new_taxonomy=self.id).values_list('old_taxonomy__scientific_name', flat=True)
            return ','.join(previous_names_list)


class TaxonVernacular(models.Model):
    """
    Common Name for Taxon i.e Species(flora/Fauna)
    Used by:
    -Taxonomy
    """
    vernacular_id = models.IntegerField(null=True, blank=True)
    vernacular_name = models.CharField(max_length=512,null=True, blank=True)
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, null=True, related_name="vernaculars")
    taxon_name_id = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'boranga'
        ordering = ['vernacular_name']

    def __str__(self):
        return str(self.vernacular_name)  # TODO: is the most appropriate?


class CrossReference(models.Model):
    """
    Previous Name(old name) of taxon which is also derived from taxon
    """
    cross_reference_id = models.IntegerField(null=True, blank=True)
    cross_reference_type = models.CharField(max_length=512,null=True, blank=True)
    old_name_id = models.IntegerField(null=True, blank=True)
    new_name_id = models.IntegerField(null=True, blank=True)
    old_taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, null=True, related_name="old_taxon")
    new_taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, null=True, related_name="new_taxon")

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.cross_reference_id)  # TODO: is the most appropriate?


class ClassificationSystem(models.Model):
    """
    Classification Suystem for a taxon

    Used by:
    -InformalGroup
    """
    classification_system_id = models.IntegerField(null=True, blank=True)
    class_type = models.CharField(max_length=100,null=True, blank=True)
    class_desc = models.CharField(max_length=100,null=True, blank=True)

    class Meta:
        app_label = 'boranga'
        ordering = ['class_desc']

    def __str__(self):
        return str(self.class_desc)  # TODO: is the most appropriate?


class InformalGroup(models.Model):
    """
    Classification informal group of taxon which is also derived from taxon
    informal_group_id is the phylo group for taxon
    """
    # may need to add the classisfication system id
    classification_system_id = models.IntegerField(null=True, blank=True)
    classification_system_fk = models.ForeignKey(ClassificationSystem, on_delete=models.CASCADE, null=True, related_name="informal_groups")
    informal_group_id = models.IntegerField(null=True, blank=True)
    taxon_name_id = models.IntegerField(null=True, blank=True)
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, null=True, related_name="informal_groups")


    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.informal_group_id)  # TODO: is the most appropriate?


class Species(models.Model):
    """
    Forms the basis for a Species and Communities record.

    Has a:
    - ConservationStatus
    - GroupType
    - SpeciesDocument
    - ConservationThreat
    - ConservationPlan
    - Taxonomy
    - Distribution
    - ConservationAttributes
    Used by:
    - Communities
    Is:
    - Table
    """

    PROCESSING_STATUS_DRAFT = 'draft'
    PROCESSING_STATUS_ACTIVE = 'active'
    PROCESSING_STATUS_HISTORICAL = 'historical'
    PROCESSING_STATUS_TO_BE_SPLIT = 'to_be_split'
    PROCESSING_STATUS_TO_BE_COMBINED = 'to_be_combined'
    PROCESSING_STATUS_TO_BE_RENAMED = 'to_be_renamed'
    PROCESSING_STATUS_CHOICES = ((PROCESSING_STATUS_DRAFT, 'Draft'),
                                 (PROCESSING_STATUS_ACTIVE, 'Active'),
                                 (PROCESSING_STATUS_HISTORICAL, 'Historical'),
                                 (PROCESSING_STATUS_TO_BE_SPLIT, 'To Be Split'),
                                 (PROCESSING_STATUS_TO_BE_COMBINED, 'To Be Combined'),
                                 (PROCESSING_STATUS_TO_BE_RENAMED, 'To Be Renamed'),
                                )
    RELATED_ITEM_CHOICES = [('species', 'species'),('conservation_status', 'Conservation Status')]
    
    species_number = models.CharField(max_length=9, blank=True, default='')
    group_type = models.ForeignKey(GroupType,
                                   on_delete=models.CASCADE)
    taxonomy = models.OneToOneField(Taxonomy, on_delete=models.SET_NULL, null=True, blank=True)
    image_doc = models.ForeignKey('SpeciesDocument', default=None, on_delete=models.CASCADE, null=True, blank=True, related_name='species_image')
    region = models.ForeignKey(Region, 
                               default=None,
                               on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, 
                                 default=None,
                                 on_delete=models.CASCADE, null=True, blank=True)
    last_data_curration_date = models.DateField(blank =True, null=True)
    processing_status = models.CharField('Processing Status', max_length=30, choices=PROCESSING_STATUS_CHOICES,
                                         default=PROCESSING_STATUS_CHOICES[0][0], null=True, blank=True)
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True, blank=True) #EmailUserRO 
    # parents will the original species  from the split/combine functionality
    parent_species = models.ManyToManyField('self', blank=True, related_name='parent')
    comment = models.CharField(max_length=500,null=True, blank=True)
    
    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return '{}'.format(self.species_number)

    def save(self, *args, **kwargs):
        cache.delete('get_species_data')
        self.full_clean()
        # Prefix "S" char to species_number.
        super(Species, self).save(*args,**kwargs)
        if self.species_number == '':
            new_species_id = 'S{}'.format(str(self.pk))
            self.species_number = new_species_id
            self.save()

    @property
    def reference(self):
        return '{}-{}'.format(self.species_number,self.species_number) #TODO : the second parameter is lodgement.sequence no. don't know yet what for species it should be
    
    @property
    def applicant(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return "{} {}".format(
                email_user.first_name,
                email_user.last_name)

    @property
    def applicant_email(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return self.email_user.email

    @property
    def applicant_details(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return "{} {}\n{}".format(
                email_user.first_name,
                email_user.last_name,
                email_user.addresses.all().first())

    @property
    def applicant_address(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return email_user.residential_address

    @property
    def applicant_id(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return self.email_user.id

    @property
    def applicant_type(self):
        if self.submitter:
            #return self.APPLICANT_TYPE_SUBMITTER
            return 'SUB'

    @property
    def applicant_field(self):
        # if self.org_applicant:
        #     return 'org_applicant'
        # elif self.proxy_applicant:
        #     return 'proxy_applicant'
        # else:
        #     return 'submitter'
        return 'submitter'

    @property
    def can_user_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        # return self.customer_status in self.CUSTOMER_EDITABLE_STATE
        user_editable_state = ['draft',]
        return self.processing_status in user_editable_state

    @property
    def can_user_view(self):
        """
        :return: True if the application is in one of the approved status.
        """
        # return self.customer_status in self.CUSTOMER_EDITABLE_STATE
        user_viewable_state = ['active','historical']
        return self.processing_status in user_viewable_state

    @property
    def can_user_action(self):
        """
        :return: True if the application is in one of the processable status for Assessor(species) role.
        """
        officer_view_state = ['draft','historical']
        if self.processing_status in officer_view_state:
            return False
        else:
            return True

    @property
    def is_discardable(self):
        """
        An application can be discarded by a customer if:
        1 - It is a draft
        2- or if the application has been pushed back to the user
        """
        # return self.customer_status == 'draft' or self.processing_status == 'awaiting_applicant_response'
        return self.processing_status == 'draft'

    @property
    def is_deletable(self):
        """
        An application can be deleted only if it is a draft and it hasn't been lodged yet
        :return:
        """
        # return self.customer_status == 'draft' and not self.species_number
        return self.processing_status == 'draft' and not self.species_number

    @property
    def is_flora_application(self):
        if self.group_type.name==GroupType.GROUP_TYPE_FLORA:
            return True
        return False

    @property
    def is_fauna_application(self):
        if self.group_type.name==GroupType.GROUP_TYPE_FAUNA:
            return True
        return False

    # used in split email template
    @property
    def child_species(self):
        child_species=Species.objects.filter(parent_species=self)
        return child_species
    
     # used in split/combine email template
    @property
    def parent_species_list(self):
        parent_species=self.parent_species.all()
        return parent_species

    @property
    def allowed_assessors(self):
        group = None
        # TODO: Take application_type into account
        # if self.processing_status in [
        #     Species.PROCESSING_STATUS_WITH_APPROVER,
        # ]:
        #     group = self.get_approver_group()
        # elif self.processing_status in [
        #     Species.PROCESSING_STATUS_WITH_REFERRAL,
        #     Species.PROCESSING_STATUS_WITH_ASSESSOR,
        # ]:
        #     group = self.get_assessor_group()
        # users = (
        #     list(
        #         map(
        #             lambda id: retrieve_email_user(id),
        #             group.get_system_group_member_ids(),
        #         )
        #     )
        #     if group
        #     else []
        # )
        # return users
        #TODO We need specific species processing SystemGroup
        group = self.get_assessor_group()
        users = (
            list(
                map(
                    lambda id: retrieve_email_user(id),
                    group.get_system_group_member_ids(),
                )
            )
            if group
            else []
        )
        return users
    @property
    def allowed_species_processors(self):
        group = None
        #TODO We need specific species processing SystemGroup
        group = self.get_species_processor_group()
        users = (
            list(
                map(
                    lambda id: retrieve_email_user(id),
                    group.get_system_group_member_ids(),
                )
            )
            if group
            else []
        )
        return users

    def get_assessor_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_ASSESSOR)

    def get_approver_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_APPROVER)
    
    def get_species_processor_group(self):
        return SystemGroup.objects.get(name=GROUP_NAME_SPECIES_COMMUNITIES_PROCESSOR)
    
    @property
    def species_processor_recipients(self):
        logger.info("species_processor_recipients")
        recipients = []
        group_ids = self.get_species_processor_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    @property
    def assessor_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_assessor_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    @property
    def approver_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_approver_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    #Check if the user is member of assessor group 
    def is_assessor(self,user):
            return user.id in self.get_assessor_group().get_system_group_member_ids()

    #Check if the user is member of assessor group for the CS Proposal
    def is_approver(self,user):
            return user.id in self.get_assessor_group().get_system_group_member_ids()
    
    def is_species_processor(self,user):
            return user.id in self.get_species_processor_group().get_system_group_member_ids()

    # def can_assess(self,user):
    #     logger.info("can assess")
    #     logger.info("user")
    #     logger.info(type(user))
    #     logger.info(user)
    #     logger.info(user.id)
    #     if self.processing_status in [
    #         "with_assessor",
    #         "with_referral",
    #     ]:
    #         logger.info("self.__assessor_group().get_system_group_member_ids()")
    #         logger.info(self.get_assessor_group().get_system_group_member_ids())
    #         return user.id in self.get_assessor_group().get_system_group_member_ids()
    #     elif self.processing_status == Species.PROCESSING_STATUS_WITH_APPROVER:
    #         return user.id in self.get_approver_group().get_system_group_member_ids()
    #     else:
    #         return False

    @property   
    def status_without_assessor(self):
        status_without_assessor = ['with_approver','approved','closed','declined','draft', 'with_referral']
        if self.processing_status in status_without_assessor:
            return True
        return False

    def has_user_edit_mode(self,user):
        officer_view_state = ['draft','historical']
        if self.processing_status in officer_view_state:
            return False
        else:
            return (
                user.id in self.get_species_processor_group().get_system_group_member_ids()
            )

    def get_related_items(self,filter_type, **kwargs):
        return_list = []
        if filter_type == 'all':
            related_field_names = ['parent_species','conservation_status',]
        else:
            related_field_names = [filter_type,]
        all_fields = self._meta.get_fields()
        for a_field in all_fields:
            if a_field.name in related_field_names:
                field_objects = []
                if a_field.is_relation:
                    if a_field.many_to_many:
                        field_objects = a_field.related_model.objects.filter(**{a_field.remote_field.name: self})
                    elif a_field.many_to_one:  # foreign key
                        field_objects = [getattr(self, a_field.name),]
                    elif a_field.one_to_many:  # reverse foreign key
                        field_objects = a_field.related_model.objects.filter(**{a_field.remote_field.name: self})
                    elif a_field.one_to_one:
                        if hasattr(self, a_field.name):
                            field_objects = [getattr(self, a_field.name),]
                for field_object in field_objects:
                    if field_object:
                        related_item = field_object.as_related_item
                        return_list.append(related_item)

        # serializer = RelatedItemsSerializer(return_list, many=True)
        # return serializer.data
        return return_list

    @property
    def as_related_item(self):
        related_item = RelatedItem(
            identifier=self.related_item_identifier,
            model_name=self._meta.verbose_name,
            descriptor=self.related_item_descriptor,
            status=self.related_item_status,
            action_url='<a href=/internal/species_communities/{}?group_type_name={} target="_blank">View</a>'.format(self.id,self.group_type.name)
        )
        return related_item

    @property
    def related_item_identifier(self):
        return self.species_number

    @property
    def related_item_descriptor(self):
        return self.taxonomy.scientific_name

    @property
    def related_item_status(self):
        return self.get_processing_status_display

    @property
    def submitter_user(self):
        email_user= retrieve_email_user(self.submitter)

        return email_user

    def log_user_action(self, action, request):
        return SpeciesUserAction.log_action(self, action, request.user.id)

    def upload_image(self, request):
        with transaction.atomic():
            document = SpeciesDocument(_file=request.data.dict()['image2'], species=self)
            document.save()
            self.image_doc=document
            self.save()

    def clone_documents(self,request):
        with transaction.atomic():
            try:
                # clone documents from original species to new species
                original_species_documents = request.data['documents']
                for doc_id in original_species_documents:
                    new_species_doc=SpeciesDocument.objects.get(id=doc_id)
                    original_species=new_species_doc.species
                    new_species_doc.species = self
                    new_species_doc.id = None
                    new_species_doc.document_number = ''
                    new_species_doc._file.name = u'boranga/species/{}/species_documents/{}'.format(self.id, new_species_doc.name)
                    new_species_doc.can_delete = True
                    new_species_doc.save()
                    new_species_doc.species.log_user_action(SpeciesUserAction.ACTION_ADD_DOCUMENT.format(new_species_doc.document_number,new_species_doc.species.species_number),request)

                    check_path = os.path.exists('private-media/boranga/species/{}/species_documents/'.format(self.id))
                    if check_path == True:
                        # copy documents on file system
                        subprocess.call('cp -p private-media/boranga/species/{}/species_documents/{}  private-media/boranga/species/{}/species_documents/'.format(original_species.id, new_species_doc.name, self.id), shell=True)
                    else:
                        # create new directory
                        os.makedirs('private-media/boranga/species/{}/species_documents/'.format(self.id), mode=0o777)
                        # then copy documents on file system
                        subprocess.call('cp -p private-media/boranga/species/{}/species_documents/{}  private-media/boranga/species/{}/species_documents/'.format(original_species.id, new_species_doc.name, self.id), shell=True)

            except:
                raise

    def clone_threats(self,request):
        with transaction.atomic():
            try:
                # clone threats from original species to new species
                original_species_threats = request.data['threats']
                for threat_id in original_species_threats:
                    new_species_threat=ConservationThreat.objects.get(id=threat_id)
                    new_species_threat.species = self
                    new_species_threat.id = None
                    new_species_threat.threat_number = ''
                    new_species_threat.save()
                    new_species_threat.species.log_user_action(SpeciesUserAction.ACTION_ADD_THREAT.format(new_species_threat.threat_number,new_species_threat.species.species_number),request)

            except:
                raise
    
    @property
    def reversion_ids(self):
        current_revision_id = Version.objects.get_for_object(self).first().revision_id
        versions = Version.objects.get_for_object(self).select_related("revision__user").filter(Q(revision__comment__icontains='status') | Q(revision_id=current_revision_id))
        version_ids = [[i.id,i.revision.date_created] for i in versions]
        return [dict(cur_version_id=version_ids[0][0], prev_version_id=version_ids[i+1][0], created=version_ids[i][1]) for i in range(len(version_ids)-1)]


class SpeciesLogDocument(Document):
    log_entry = models.ForeignKey('SpeciesLogEntry',related_name='documents', on_delete=models.CASCADE)
    _file = models.FileField(upload_to=update_species_comms_log_filename, max_length=512, storage=private_storage)

    class Meta:
        app_label = 'boranga'


class SpeciesLogEntry(CommunicationsLogEntry):
    species = models.ForeignKey(Species, related_name='comms_logs', on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.reference, self.subject)

    class Meta:
        app_label = 'boranga'

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.species.reference
        super(SpeciesLogEntry, self).save(**kwargs)

class SpeciesUserAction(UserAction):
    
    ACTION_EDIT_SPECIES= "Edit Species {}"
    ACTION_CREATE_SPECIES= "Create new species {}"
    ACTION_SAVE_SPECIES = "Save Species {}"
    ACTION_IMAGE_UPDATE= "Species Image document updated for Species {}"
    ACTION_IMAGE_DELETE= "Species Image document deleted for Species {}"

    # Document
    ACTION_ADD_DOCUMENT= "Document {} added for Species {}"
    ACTION_UPDATE_DOCUMENT= "Document {} updated for Species {}"
    ACTION_DISCARD_DOCUMENT= "Document {} discarded for Species {}"
    ACTION_REINSTATE_DOCUMENT= "Document {} reinstated for Species {}"

    # Threat
    ACTION_ADD_THREAT= "Threat {} added for Species {}"
    ACTION_UPDATE_THREAT= "Threat {} updated for Species {}"
    ACTION_DISCARD_THREAT= "Threat {} discarded for Species {}"
    ACTION_REINSTATE_THREAT= "Threat {} reinstated for Species {}"

    ACTION_CLOSE_CONSERVATIONSTATUS = "De list species {}"
    ACTION_DISCARD_PROPOSAL = "Discard species proposal {}"

    class Meta:
        app_label = 'boranga'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, species, action, user):
        return cls.objects.create(
            species=species,
            who=user,
            what=str(action)
        )

    species = models.ForeignKey(Species, related_name='action_logs', on_delete=models.CASCADE)


class SpeciesDistribution(models.Model):
    """
    All the different locations where this species can be found.

    Used by:
    - Species
    Is:
    - Table
    """
    department_file_numbers = models.CharField(max_length=512,null=True, blank=True)  # objective, legacy, list of things
    number_of_occurrences = models.IntegerField(null=True, blank=True)
    noo_auto = models.BooleanField(default=True) # to check auto or manual entry of number_of_occurrences
    extent_of_occurrences = models.IntegerField(null = True, blank=True)
    eoo_auto = models.BooleanField(default=True) # extra boolean field to check auto or manual entry of extent_of_occurrences
    area_of_occupancy = models.IntegerField(null=True, blank=True)
    aoo_auto = models.BooleanField(default=True) # to check auto or manual entry of area_of_occupancy
    area_of_occupancy_actual = models.IntegerField(null=True, blank=True)
    aoo_actual_auto = models.BooleanField(default=True) # to check auto or manual entry of area_of_occupancy_actual
    number_of_iucn_locations = models.IntegerField(null=True, blank=True)
    number_of_iucn_subpopulations = models.IntegerField(null=True, blank=True)
    species = models.OneToOneField(Species, on_delete=models.CASCADE, null=True, related_name="species_distribution")

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.id)  # TODO: is the most appropriate?


class Community(models.Model):
    """
    A collection of 2 or more Species within a specific location.

    Has a:
    - GroupType
    - Species
    Used by:
    - N/A
    Is:
    - Table
    """
    PROCESSING_STATUS_DRAFT = 'draft'
    PROCESSING_STATUS_ACTIVE = 'active'
    PROCESSING_STATUS_HISTORICAL = 'historical'
    PROCESSING_STATUS_TO_BE_SPLIT = 'to_be_split'
    PROCESSING_STATUS_TO_BE_COMBINED = 'to_be_combined'
    PROCESSING_STATUS_TO_BE_RENAMED = 'to_be_renamed'
    PROCESSING_STATUS_CHOICES = ((PROCESSING_STATUS_DRAFT, 'Draft'),
                                 (PROCESSING_STATUS_ACTIVE, 'Active'),
                                 (PROCESSING_STATUS_HISTORICAL, 'Historical'),
                                 (PROCESSING_STATUS_TO_BE_SPLIT, 'To Be Split'),
                                 (PROCESSING_STATUS_TO_BE_COMBINED, 'To Be Combined'),
                                 (PROCESSING_STATUS_TO_BE_RENAMED, 'To Be Renamed'),
                                )
    # RELATED_ITEM_CHOICES = [('species', 'Species'), ('conservation_status', 'Conservation Status')]
    RELATED_ITEM_CHOICES = [('conservation_status', 'Conservation Status')]

    community_number = models.CharField(max_length=9, blank=True, default='')
    group_type = models.ForeignKey(GroupType,on_delete=models.CASCADE)
    # TODO the species is noy required as per the new requirements
    species = models.ManyToManyField(Species, blank=True)
    # taxonomy = models.ForeignKey(CommunityTaxonomy, on_delete=models.SET_NULL, unique=True, null=True, blank=True)
    region = models.ForeignKey(Region, 
                               default=None,
                               on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, 
                                 default=None,
                                 on_delete=models.CASCADE, null=True, blank=True)
    last_data_curration_date = models.DateField(blank =True, null=True)
    submitter = models.IntegerField(null=True) #EmailUserRO 
    image_doc = models.ForeignKey('CommunityDocument', default=None, on_delete=models.CASCADE, null=True, blank=True, related_name='community_image')
    processing_status = models.CharField('Processing Status', max_length=30, choices=PROCESSING_STATUS_CHOICES,
                                         default=PROCESSING_STATUS_CHOICES[0][0])
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
    lodgement_date = models.DateTimeField(blank=True, null=True) # TODO confirm if proposed date is the same or different
    # TODO not be used as the taxonomy will be editable for community
    comment = models.CharField(max_length=500,null=True, blank=True)

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return '{}'.format(self.community_number)

    def save(self, *args, **kwargs):
        # Prefix "C" char to community_number.
        super(Community, self).save(*args,**kwargs)
        if self.community_number == '':
            new_community_id = 'C{}'.format(str(self.pk))
            self.community_number = new_community_id
            self.save()
    
    @property
    def applicant(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return "{} {}".format(
                email_user.first_name,
                email_user.last_name)

    @property
    def applicant_email(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return self.email_user.email

    @property
    def applicant_details(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return "{} {}\n{}".format(
                email_user.first_name,
                email_user.last_name,
                email_user.addresses.all().first())

    @property
    def applicant_address(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return email_user.residential_address

    @property
    def applicant_id(self):
        if self.submitter:
            email_user = retrieve_email_user(self.submitter)
            return self.email_user.id

    @property
    def applicant_type(self):
        if self.submitter:
            #return self.APPLICANT_TYPE_SUBMITTER
            return 'SUB'

    @property
    def applicant_field(self):
        # if self.org_applicant:
        #     return 'org_applicant'
        # elif self.proxy_applicant:
        #     return 'proxy_applicant'
        # else:
        #     return 'submitter'
        return 'submitter'

    @property
    def can_user_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        # return self.customer_status in self.CUSTOMER_EDITABLE_STATE
        user_editable_state = ['draft',]
        return self.processing_status in user_editable_state

    @property
    def can_user_view(self):
        """
        :return: True if the application is in one of the approved status.
        """
        # return self.customer_status in self.CUSTOMER_EDITABLE_STATE
        user_viewable_state = ['active','historical']
        return self.processing_status in user_viewable_state

    @property
    def can_user_action(self):
        """
        :return: True if the application is in one of the processable status for Assessor(species) role.
        """
        officer_view_state = ['draft','historical']
        if self.processing_status in officer_view_state:
            return False
        else:
            return True

    @property
    def is_discardable(self):
        """
        An application can be discarded by a customer if:
        1 - It is a draft
        2- or if the application has been pushed back to the user
        """
        # return self.customer_status == 'draft' or self.processing_status == 'awaiting_applicant_response'
        return self.processing_status == 'draft'

    @property
    def is_deletable(self):
        """
        An application can be deleted only if it is a draft and it hasn't been lodged yet
        :return:
        """
        # return self.customer_status == 'draft' and not self.community_number
        return self.processing_status == 'draft' and not self.community_number

    @property
    def is_community_application(self):
        if self.group_type.name==GroupType.GROUP_TYPE_COMMUNITY:
            return True
        return False

    @property
    def allowed_assessors(self):
        group = None
        # # TODO: Take application_type into account
        # if self.processing_status in [
        #     Community.PROCESSING_STATUS_WITH_APPROVER,
        # ]:
        #     group = self.get_approver_group()
        # elif self.processing_status in [
        #     Community.PROCESSING_STATUS_WITH_REFERRAL,
        #     Community.PROCESSING_STATUS_WITH_ASSESSOR,
        # ]:
        #     group = self.get_assessor_group()
        group = self.get_assessor_group()
        users = (
            list(
                map(
                    lambda id: retrieve_email_user(id),
                    group.get_system_group_member_ids(),
                )
            )
            if group
            else []
        )
        return users

    @property
    def allowed_community_processors(self):
        group = None
        group = self.get_community_processor_group()
        users = (
            list(
                map(
                    lambda id: retrieve_email_user(id),
                    group.get_system_group_member_ids(),
                )
            )
            if group
            else []
        )
        return users

    def get_assessor_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_ASSESSOR)

    def get_approver_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_APPROVER)

    # Group for editing the Approved CS(only specific fields)
    def get_editor_group(self):
        return SystemGroup.objects.get(name=GROUP_NAME_EDITOR)

    def get_community_processor_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_SPECIES_COMMUNITIES_PROCESSOR)

    @property
    def assessor_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_assessor_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    @property
    def approver_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_approver_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    @property
    def community_processor_recipients(self):
        logger.info("acommunity_processor_recipients")
        recipients = []
        group_ids = self.get_community_processor_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    #Check if the user is member of assessor group for the CS Proposal
    def is_assessor(self,user):
            return user.id in self.get_assessor_group().get_system_group_member_ids()

    #Check if the user is member of assessor group for the CS Proposal
    def is_approver(self,user):
            return user.id in self.get_assessor_group().get_system_group_member_ids()

    #Check if the user is member of processor group
    def is_community_processor(self,user):
            return user.id in self.get_community_processor_group().get_system_group_member_ids()

    # def can_assess(self,user):
    #     logger.info("can assess")
    #     logger.info("user")
    #     logger.info(type(user))
    #     logger.info(user)
    #     logger.info(user.id)
    #     if self.processing_status in [
    #         # "on_hold",
    #         # "with_qa_officer",
    #         "with_assessor",
    #         "with_referral",
    #         "with_assessor_conditions",
    #     ]:
    #         logger.info("self.__assessor_group().get_system_group_member_ids()")
    #         logger.info(self.get_assessor_group().get_system_group_member_ids())
    #         return user.id in self.get_assessor_group().get_system_group_member_ids()
    #     elif self.processing_status == Community.PROCESSING_STATUS_WITH_APPROVER:
    #         return user.id in self.get_approver_group().get_system_group_member_ids()
    #     else:
    #         return False

    @property   
    def status_without_assessor(self):
        status_without_assessor = ['with_approver','approved','closed','declined','draft', 'with_referral']
        if self.processing_status in status_without_assessor:
            return True
        return False

    def has_user_edit_mode(self,user):
        officer_view_state = ['draft','historical']
        if self.processing_status in officer_view_state:
            return False
        else:
            return (
                user.id in self.get_community_processor_group().get_system_group_member_ids()
            )

    @property
    def reference(self):
        return '{}-{}'.format(self.community_number, self.community_number)
    
    def get_related_items(self,filter_type, **kwargs):
        return_list = []
        if filter_type == 'all':
            related_field_names = ['species', 'conservation_status',]
        else:
            related_field_names = [filter_type,]
        all_fields = self._meta.get_fields()
        for a_field in all_fields:
            if a_field.name in related_field_names:
                field_objects = []
                if a_field.is_relation:
                    if a_field.many_to_many:
                        field_objects = a_field.related_model.objects.filter(**{a_field.remote_field.name: self})
                    elif a_field.many_to_one:  # foreign key
                        field_objects = [getattr(self, a_field.name),]
                    elif a_field.one_to_many:  # reverse foreign key
                        field_objects = a_field.related_model.objects.filter(**{a_field.remote_field.name: self})
                    elif a_field.one_to_one:
                        if hasattr(self, a_field.name):
                            field_objects = [getattr(self, a_field.name),]
                for field_object in field_objects:
                    if field_object:
                        related_item = field_object.as_related_item
                        return_list.append(related_item)

        # serializer = RelatedItemsSerializer(return_list, many=True)
        # return serializer.data
        return return_list

    @property
    def as_related_item(self):
        related_item = RelatedItem(
            identifier=self.related_item_identifier,
            model_name=self._meta.verbose_name,
            descriptor=self.related_item_descriptor,
            status=self.related_item_status,
            action_url='<a href=/internal/species_communities/{} target="_blank">Open</a>'.format(self.id)
        )
        return related_item

    @property
    def related_item_identifier(self):
        return self.community_number

    @property
    def related_item_descriptor(self):
        return  CommunityTaxonomy.objects.get(community=self).community_name

    @property
    def related_item_status(self):
        return self.processing_status

    def log_user_action(self, action, request):
        return CommunityUserAction.log_action(self, action, request.user.id)

    def upload_image(self, request):
        with transaction.atomic():
            document = CommunityDocument(_file=request.data.dict()['image2'], community=self)
            document.save()
            self.image_doc=document
            self.save()

    @property
    def reversion_ids(self):
        current_revision_id = Version.objects.get_for_object(self).first().revision_id
        versions = Version.objects.get_for_object(self).select_related("revision__user").filter(Q(revision__comment__icontains='status') | Q(revision_id=current_revision_id))
        version_ids = [[i.id,i.revision.date_created] for i in versions]
        return [dict(cur_version_id=version_ids[0][0], prev_version_id=version_ids[i+1][0], created=version_ids[i][1]) for i in range(len(version_ids)-1)]

class CommunityTaxonomy(models.Model):
    """
    Description from wacensus, to get the main name then fill in everything else

    Has a:
    Used by:
    - Community
    Is:
    - Table
    """
    community = models.OneToOneField(Community, on_delete=models.CASCADE, null=True, related_name="taxonomy")
    community_migrated_id = models.CharField(max_length=200, null=True, blank=True)
    community_name = models.CharField(max_length=512,null=True, blank=True)
    community_description = models.CharField(max_length=2048, null=True, blank=True)
    name_currency = models.CharField(max_length=16, null=True, blank=True) # is it the is_current name? true or false
    previous_name = models.CharField(max_length=512,null=True, blank=True)
    name_authority = models.CharField(max_length=500,null=True, blank=True)
    name_comments = models.CharField(max_length=500,null=True, blank=True)

    class Meta:
        app_label = 'boranga'
        ordering = ['community_name']

    def __str__(self):
        return str(self.community_name)  # TODO: is the most appropriate?


class CommunityLogDocument(Document):
    log_entry = models.ForeignKey('CommunityLogEntry',related_name='documents', on_delete=models.CASCADE)
    _file = models.FileField(upload_to=update_community_comms_log_filename, max_length=512, storage=private_storage)

    class Meta:
        app_label = 'boranga'


class CommunityLogEntry(CommunicationsLogEntry):
    community = models.ForeignKey(Community, related_name='comms_logs', on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.reference, self.subject)

    class Meta:
        app_label = 'boranga'

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.community.reference
        super(CommunityLogEntry, self).save(**kwargs)

class CommunityUserAction(UserAction):
    
    ACTION_EDIT_COMMUNITY= "Edit Community {}"
    ACTION_CREATE_COMMUNITY= "Create new community {}"
    ACTION_SAVE_COMMUNITY = "Save Community {}"
    ACTION_IMAGE_UPDATE= "Community Image document updated for Community {}"
    ACTION_IMAGE_DELETE= "Community Image document deleted for Community {}"

    # Document
    ACTION_ADD_DOCUMENT= "Document {} uploaded for Community {}"
    ACTION_UPDATE_DOCUMENT= "Document {} updated for Community {}"
    ACTION_DISCARD_DOCUMENT= "Document {} discarded for Community {}"
    ACTION_REINSTATE_DOCUMENT= "Document {} reinstated for Community {}"

    # Threat
    ACTION_ADD_THREAT= "Threat {} added for Community {}"
    ACTION_UPDATE_THREAT= "Threat {} updated for Community {}"
    ACTION_DISCARD_THREAT= "Threat {} discarded for Community {}"
    ACTION_REINSTATE_THREAT= "Threat {} reinstated for Community {}"



    class Meta:
        app_label = 'boranga'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, community, action, user):
        return cls.objects.create(
            community=community,
            who=user,
            what=str(action)
        )

    community = models.ForeignKey(Community, related_name='action_logs', on_delete=models.CASCADE)


class CommunityDistribution(models.Model):
    """
    All the different locations where this community can be found.

    Used by:
    - Communities
    Is:
    - Table
    """
    department_file_numbers = models.CharField(max_length=512,null=True, blank=True)  # objective, legacy, list of things
    number_of_occurrences = models.IntegerField(null=True, blank=True)
    noo_auto = models.BooleanField(default=True) # to check auto or manual entry of number_of_occurrences
    extent_of_occurrences = models.IntegerField(null = True, blank=True)
    eoo_auto = models.BooleanField(default=True) # extra boolean field to check auto or manual entry of extent_of_occurrences
    area_of_occupancy = models.IntegerField(null=True, blank=True)
    aoo_auto = models.BooleanField(default=True) # to check auto or manual entry of area_of_occupancy
    area_of_occupancy_actual = models.IntegerField(null=True, blank=True)
    aoo_actual_auto = models.BooleanField(default=True) # to check auto or manual entry of area_of_occupancy_actual
    number_of_iucn_locations = models.IntegerField(null=True, blank=True)
    number_of_iucn_subpopulations = models.IntegerField(null=True, blank=True)
    # Community Ecological Attributes
    community_original_area = models.IntegerField(null=True, blank=True)
    community_original_area_accuracy = models.IntegerField(null=True, blank=True)
    community_original_area_reference = models.CharField(max_length=512, null=True, blank=True)
    community = models.OneToOneField(Community, on_delete=models.CASCADE, null=True, related_name="community_distribution")

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.id)  # TODO: is the most appropriate?


class DocumentCategory(models.Model):
    """
    This is particularly useful for organisation of documents e.g. preventing inappropriate documents being added
    to certain tables.

    Used by:
    - DocumentSubCategory
    - SpeciesDocument
    - CommunityDocument
    -ConservationStatusDocument
    Is:
    - Table
    """
    document_category_name = models.CharField(max_length=128, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ['document_category_name']

    def __str__(self):
        return str(self.document_category_name)


class DocumentSubCategory(models.Model):
    """
    This is particularly useful for organisation of sub documents e.g. preventing inappropriate documents being added
    to certain tables.

    Used by:
    - SpeciesDocument
    - CommunityDocument
    -ConservationStatusDocument
    Is:
    - Table
    """
    document_category = models.ForeignKey(DocumentCategory, 
                                          on_delete=models.CASCADE,
                                          related_name='document_sub_categories')
    document_sub_category_name = models.CharField(max_length=128, unique=True,)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Document Sub Category"
        verbose_name_plural = "Document Sub Categories"
        ordering = ['document_sub_category_name']

    def __str__(self):
        return str(self.document_sub_category_name)
                                    

class SpeciesDocument(Document):
    """
    Meta-data associated with a document relevant to a Species.

    Has a:
    - Species
    - DocumentCategory
    - DocumentSubCategoty
    Used for:
    - Species
    Is:
    - Table
    """
    document_number = models.CharField(max_length=9, blank=True, default='')
    _file = models.FileField(upload_to=update_species_doc_filename, max_length=512, default="None", storage=private_storage)
    input_name = models.CharField(max_length=255,null=True,blank=True)
    can_delete = models.BooleanField(default=True) # after initial submit prevent document from being deleted
    visible = models.BooleanField(default=True) # to prevent deletion on file system, hidden and still be available in history 
    document_category = models.ForeignKey(DocumentCategory, 
                                          null=True,
                                          blank=True,
                                          on_delete=models.SET_NULL)
    document_sub_category = models.ForeignKey(DocumentSubCategory, 
                                          null=True,
                                          blank=True,
                                          on_delete=models.SET_NULL)
    species = models.ForeignKey(Species, 
                                blank=False, 
                                default=None,
                                on_delete=models.CASCADE,
                                related_name='species_documents')

    class Meta:
        app_label = 'boranga'
        verbose_name = "Species Document"

    def save(self, *args, **kwargs):
        # Prefix "D" char to document_number.
        super(SpeciesDocument, self).save(*args,**kwargs)
        if self.document_number == '':
            new_document_id = 'D{}'.format(str(self.pk))
            self.document_number = new_document_id
            self.save()

    def add_documents(self, request):
        with transaction.atomic():
            try:
                # save the files
                data = json.loads(request.data.get('data'))
                # if not data.get('update'):
                #     documents_qs = self.filter(input_name='species_doc', visible=True)
                #     documents_qs.delete()
                for idx in range(data['num_files']):
                    _file = request.data.get('file-'+str(idx))
                    self._file=_file
                    self.name=_file.name
                    self.input_name = data['input_name']
                    self.can_delete = True
                    self.save()
                # end save documents
                self.save()
            except:
                raise
        return


class CommunityDocument(Document):
    """
    Meta-data associated with a document relevant to a Community.

    Has a:
    - Community
    - DocumentCategory
    - DocumentSubCategory
    Used for:
    - Community:
    Is:
    - Table
    """
    document_number = models.CharField(max_length=9, blank=True, default='')
    _file = models.FileField(upload_to=update_community_doc_filename, max_length=512, default="None", storage=private_storage)
    input_name = models.CharField(max_length=255,null=True,blank=True)
    can_delete = models.BooleanField(default=True) # after initial submit prevent document from being deleted
    visible = models.BooleanField(default=True) # to prevent deletion on file system, hidden and still be available in history 
    document_category = models.ForeignKey(DocumentCategory, 
                                          null=True,
                                          blank=True,
                                          on_delete=models.SET_NULL)
    document_sub_category = models.ForeignKey(DocumentSubCategory, 
                                          null=True,
                                          blank=True,
                                          on_delete=models.SET_NULL)
    community = models.ForeignKey(Community, 
                                blank=False, 
                                default=None,
                                on_delete=models.CASCADE,
                                related_name='community_documents')

    class Meta:
        app_label = 'boranga'
        verbose_name = "Community Document"

    def save(self, *args, **kwargs):
        # Prefix "D" char to document_number.
        super(CommunityDocument, self).save(*args,**kwargs)
        if self.document_number == '':
            new_document_id = 'D{}'.format(str(self.pk))
            self.document_number = new_document_id
            self.save()
    
    def add_documents(self, request):
        with transaction.atomic():
            try:
                # save the files
                data = json.loads(request.data.get('data'))
                # if not data.get('update'):
                #     documents_qs = self.filter(input_name='species_doc', visible=True)
                #     documents_qs.delete()
                for idx in range(data['num_files']):
                    _file = request.data.get('file-'+str(idx))
                    self._file=_file
                    self.name=_file.name
                    self.input_name = data['input_name']
                    self.can_delete = True
                    self.save()
                # end save documents
                self.save()
            except:
                raise
        return


class ThreatCategory(models.Model):
    """
    # e.g. mechnical disturbance
    """
    name = models.CharField(max_length=128, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Threat Category"
        verbose_name_plural = "Threat Categories"

    def __str__(self):
        return str(self.name)


class CurrentImpact(models.Model):
    """
    # don't know the data yet

    Used by:
    - ConservationThreat

    """
    name = models.CharField(max_length=100, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Current Impact"
        verbose_name_plural = "Current Impacts"

    def __str__(self):
        return str(self.name)


class PotentialImpact(models.Model):
    """
    # don't know the data yet
    
    Used by:
    - ConservationThreat

    """
    name = models.CharField(max_length=100, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Potential Impact"
        verbose_name_plural = "Potential Impacts"

    def __str__(self):
        return str(self.name)


class PotentialThreatOnset(models.Model):
    """
    # don't know the data yet
    
    Used by:
    - ConservationThreat

    """
    name = models.CharField(max_length=100, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Potential Threat Onset"
        verbose_name_plural = "Potential Threat Onsets"

    def __str__(self):
        return str(self.name)


class ThreatAgent(models.Model):
    """
    Used by:
    - ConservationThreat

    """
    name = models.CharField(max_length=100, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Threat Agent"
        verbose_name_plural = "Threat Agents"

    def __str__(self):
        return str(self.name)


class ConservationThreat(models.Model):
    """
    Threat for a species and community in a particular location.

    NB: Maybe make many to many

    Has a:
    - species
    - community
    Used for:
    - Species
    - Community
    Is:
    - Table
    """
    species = models.ForeignKey(Species, on_delete=models.CASCADE, null=True, blank=True , related_name="species_threats")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True, related_name="community_threats")
    threat_number = models.CharField(max_length=9, blank=True, default='')
    threat_category = models.ForeignKey(ThreatCategory, on_delete=models.CASCADE, default=None, null=True, blank=True)
    threat_agent = models.ForeignKey(ThreatAgent, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    current_impact = models.ForeignKey(CurrentImpact, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    potential_impact = models.ForeignKey(PotentialImpact, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    potential_threat_onset = models.ForeignKey(PotentialThreatOnset, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    comment = models.CharField(max_length=512,
                               default="None")
    date_observed = models.DateField(blank =True, null=True)
    visible = models.BooleanField(default=True) # to prevent deletion, hidden and still be available in history


    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.id)  # TODO: is the most appropriate?

    def save(self, *args, **kwargs):
        super(ConservationThreat, self).save(*args,**kwargs)
        if self.threat_number == '':
            new_threat_id = 'T{}'.format(str(self.pk))
            self.threat_number = new_threat_id
            self.save()

    @property
    def source(self):
        if self.species:
            return self.species.id
        elif self.community:
            return self.community.id


class FloraRecruitmentType(models.Model):
    """
    # list derived from WACensus

    Used by:
    - SpeciesConservationAttributes

    """
    recruitment_type = models.CharField(max_length=200, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Flora Recruitment Type"
        verbose_name_plural = "Flora Recruitment Types"
        ordering = ['recruitment_type']

    def __str__(self):
        return str(self.recruitment_type)


class RootMorphology(models.Model):
    """
    # list derived from WACensus

    Used by:
    - SpeciesConservationAttributes

    """
    name = models.CharField(max_length=200, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Root Morphology"
        verbose_name_plural = "Root Morphologies"
        ordering = ['name']

    def __str__(self):
        return str(self.name)


class PostFireHabitatInteraction(models.Model):
    """
    # list derived from WACensus

    Used by:
    - SpeciesConservationAttributes

    """
    name = models.CharField(max_length=200, blank=False, unique=True)

    class Meta:
        app_label = 'boranga'
        verbose_name = "Post Fire Habitat Interaction"
        verbose_name_plural = "Post Fire Habitat Interactions"
        ordering = ['name']

    def __str__(self):
        return str(self.name)


class SpeciesConservationAttributes(models.Model):
    """
    Species conservation attributes data.

    Used for:
    - Species
    Is:
    - Table
    """
    PERIOD_CHOICES = ((1, 'January'),
                    (2, 'February'),
                    (3, 'March'),
                    (4, 'April'),
                    (5, 'May'),
                    (6, 'June'),
                    (7, 'July'),
                    (8, 'August'),
                    (9, 'September'),
                    (10, 'October'),
                    (11, 'November'),
                    (12, 'December'),
                    )
    INTERVAL_CHOICES = ((1, 'year/s'),
                    (2, 'month/s')
                    )

    species = models.OneToOneField(Species, on_delete=models.CASCADE, null=True, related_name="species_conservation_attributes")
    
    # flora related attributes
    flowering_period = MultiSelectField(max_length=250, blank=True, choices=PERIOD_CHOICES, null=True)
    fruiting_period = MultiSelectField(max_length=250, blank=True, choices=PERIOD_CHOICES, null=True)
    flora_recruitment_type = models.ForeignKey(FloraRecruitmentType, on_delete=models.SET_NULL, null=True, blank=True)
    flora_recruitment_notes = models.CharField(max_length=1000,null=True, blank=True)
    seed_viability_germination_info = models.CharField(max_length=1000,null=True, blank=True)
    root_morphology = models.ForeignKey(RootMorphology, on_delete=models.SET_NULL, null=True, blank=True)
    pollinator_information = models.CharField(max_length=1000,null=True, blank=True)
    response_to_dieback = models.CharField(max_length=1500, null=True, blank=True)

    # fauna related attributes
    breeding_period = MultiSelectField(max_length=250, blank=True, choices=PERIOD_CHOICES, null=True)
    fauna_breeding = models.CharField(max_length=2000,null=True, blank=True)
    fauna_reproductive_capacity = models.CharField(max_length=200,null=True, blank=True)
    diet_and_food_source = models.CharField(max_length=500, null=True, blank=True)
    home_range = models.CharField(max_length=1000, null=True, blank=True)

    # flora and fauna common attributes
    habitat_growth_form = models.CharField(max_length=200,null=True, blank=True)
    time_to_maturity_from = models.IntegerField(null=True, blank=True)
    time_to_maturity_to = models.IntegerField(null=True, blank=True)
    time_to_maturity_choice = models.CharField(max_length=10, choices=INTERVAL_CHOICES, null=True, blank=True)
    generation_length_from = models.IntegerField(null=True, blank=True)
    generation_length_to = models.IntegerField(null=True, blank=True)
    generation_length_choice = models.CharField(max_length=10, choices=INTERVAL_CHOICES, null=True, blank=True)
    average_lifespan_from = models.IntegerField(null=True, blank=True)
    average_lifespan_to = models.IntegerField(null=True, blank=True)
    average_lifespan_choice = models.CharField(max_length=10, choices=INTERVAL_CHOICES, null=True, blank=True)
    minimum_fire_interval_from = models.IntegerField(null=True, blank=True) 
    minimum_fire_interval_to = models.IntegerField(null=True, blank=True)
    minimum_fire_interval_choice = models.CharField(max_length=10, choices=INTERVAL_CHOICES, null=True, blank=True)
    response_to_fire = models.CharField(max_length=200, null=True, blank=True)
    post_fire_habitat_interaction = models.ForeignKey(PostFireHabitatInteraction, on_delete=models.SET_NULL, null=True, blank=True)
    # TODO Remove the response to dist field
    response_to_disturbance = models.CharField(max_length=500, null=True, blank=True)
    habitat = models.CharField(max_length=1000, null=True, blank=True)
    hydrology = models.CharField(max_length=200, null=True, blank=True)
    research_requirements = models.CharField(max_length=1500, null=True, blank=True)
    other_relevant_diseases = models.CharField(max_length=1500, null=True, blank=True)


    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.species)  # TODO: is the most appropriate?


class CommunityConservationAttributes(models.Model):
    """
    Community conservation attributes data.

    Used for:
    - Community
    Is:
    - Table
    """
    community = models.OneToOneField(Community, on_delete=models.CASCADE, null=True, related_name="community_conservation_attributes")

    # habitat_growth_form = models.CharField(max_length=200,null=True, blank=True)
    pollinator_information = models.CharField(max_length=1000,null=True, blank=True)
    minimum_fire_interval_from = models.IntegerField(null=True, blank=True)
    minimum_fire_interval_to = models.IntegerField(null=True, blank=True)
    minimum_fire_interval_choice = models.CharField(max_length=10, choices=SpeciesConservationAttributes.INTERVAL_CHOICES, null=True, blank=True)
    response_to_fire = models.CharField(max_length=200, null=True, blank=True)
    post_fire_habitat_interaction = models.ForeignKey(PostFireHabitatInteraction, on_delete=models.SET_NULL, null=True, blank=True)
    hydrology = models.CharField(max_length=200, null=True, blank=True)
    ecological_and_biological_information = models.CharField(max_length=500, null=True, blank=True)
    research_requirements = models.CharField(max_length=500, null=True, blank=True)
    response_to_dieback = models.CharField(max_length=500, null=True, blank=True)
    other_relevant_diseases = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        app_label = 'boranga'

    def __str__(self):
        return str(self.community)  # TODO: is the most appropriate?

import reversion
reversion.register(Species)
reversion.register(Community)