import nested_admin
from django.contrib.gis import admin, forms
from ordered_model.admin import OrderedModelAdmin

from boranga.admin import (
    ArchivableModelAdminMixin,
    CsvExportMixin,
    DeleteProtectedModelAdmin,
)
from boranga.components.occurrence.models import (
    AnimalHealth,
    BufferGeometry,
    CoordinateSource,
    CountedSubject,
    Datum,
    DeathReason,
    Drainage,
    IdentificationCertainty,
    Intensity,
    LandForm,
    LocationAccuracy,
    ObservationMethod,
    ObserverCategory,
    ObserverRole,
    OccurrenceGeometry,
    OccurrenceReportBulkImportSchema,
    OccurrenceReportBulkImportSchemaColumn,
    OccurrenceReportBulkImportTask,
    OccurrenceReportGeometry,
    OccurrenceSite,
    OccurrenceTenure,
    OccurrenceTenurePurpose,
    OccurrenceTenureVesting,
    PermitType,
    PlantCondition,
    PlantCountAccuracy,
    PlantCountMethod,
    PrimaryDetectionMethod,
    ReproductiveState,
    RockType,
    SampleDestination,
    SampleType,
    SecondarySign,
    SiteType,
    SoilColour,
    SoilCondition,
    SoilType,
    WildStatus,
)
from boranga.components.spatial.utils import wkb_to_geojson


class GeometryField(forms.GeometryField):
    widget = forms.OSMWidget(
        attrs={
            "display_raw": False,
            "map_width": 800,
            "map_srid": 4326,
            "map_height": 600,
            "default_lat": -31.9502682,
            "default_lon": 115.8590241,
        }
    )


class OccurrenceTenureInline(nested_admin.NestedTabularInline):
    model = OccurrenceTenure
    extra = 0
    verbose_name = "Occurrence Geometry Tenure Area"
    verbose_name_plural = "Occurrence Geometry Tenure Areas"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "tenure_area_id",
                    "status",
                    "owner_name",
                    "owner_count",
                    "purpose",
                    "significant_to_occurrence",
                    "comments",
                )
            },
        ),
    )

    readonly_fields = ["tenure_area_id"]


class BufferGeometryInlineForm(forms.ModelForm):
    geometry = GeometryField()

    class Meta:
        model = BufferGeometry
        fields = "__all__"


class BufferGeometryInline(nested_admin.NestedStackedInline):
    model = BufferGeometry
    form = BufferGeometryInlineForm
    extra = 0

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "geometry",
                    ("original_geometry"),
                    (
                        "area_sqm",
                        "area_sqhm",
                    ),
                    (
                        "object_id",
                        "content_type",
                        "created_from",
                        "source_of",
                    ),
                    (
                        "color",
                        "stroke",
                    ),
                )
            },
        ),
    )

    readonly_fields = [
        "original_geometry",
        "area_sqm",
        "area_sqhm",
        "object_id",
        "content_type",
        "created_from",
        "source_of",
    ]


class OccurrenceReportGeometryInlineForm(forms.ModelForm):
    geometry = GeometryField()

    class Meta:
        model = OccurrenceReportGeometry
        fields = "__all__"


class OccurrenceReportGeometryInline(admin.StackedInline):
    model = OccurrenceReportGeometry
    form = OccurrenceReportGeometryInlineForm
    extra = 0
    verbose_name = "Occurrence Report Geometry"
    verbose_name_plural = "Occurrence Report Geometries"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "geometry",
                    ("original_geometry"),
                    (
                        "area_sqm",
                        "area_sqhm",
                    ),
                    (
                        "locked",
                        "show_on_map",
                    ),
                    (
                        # "copied_from",
                        "drawn_by",
                    ),
                    (
                        "object_id",
                        "content_type",
                        "created_from",
                        "source_of",
                    ),
                    (
                        "color",
                        "stroke",
                    ),
                )
            },
        ),
    )

    readonly_fields = [
        "original_geometry",
        "area_sqm",
        "area_sqhm",
        "object_id",
        "content_type",
        "created_from",
        "source_of",
    ]


class OccurrenceGeometryInlineForm(forms.ModelForm):
    geometry = GeometryField()

    class Meta:
        model = OccurrenceGeometry
        fields = "__all__"


# class


class OccurrenceGeometryInline(nested_admin.NestedStackedInline):
    model = OccurrenceGeometry
    form = OccurrenceGeometryInlineForm
    extra = 0
    verbose_name = "Occurrence Geometry"
    verbose_name_plural = "Occurrence Geometries"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "geometry",
                    ("original_geometry"),
                    (
                        "area_sqm",
                        "area_sqhm",
                    ),
                    ("locked",),
                    (
                        "created_date",
                        "updated_date",
                    ),
                    (
                        # "copied_from",
                        "drawn_by",
                    ),
                    ("buffer_radius",),
                    (
                        "object_id",
                        "content_type",
                        "created_from",
                        "source_of",
                    ),
                    (
                        "color",
                        "stroke",
                    ),
                )
            },
        ),
    )

    readonly_fields = [
        "original_geometry",
        "area_sqm",
        "area_sqhm",
        "object_id",
        "content_type",
        "created_from",
        "source_of",
    ]

    inlines = [BufferGeometryInline, OccurrenceTenureInline]


class OccurrenceTenureAdminForm(forms.ModelForm):
    # geometry = forms.GeometryField(widget=forms.OSMWidget(attrs={"display_raw": False}))

    class Meta:
        model = OccurrenceTenure
        fields = "__all__"


@admin.register(OccurrenceTenure)
class OccurrenceTenureAdmin(nested_admin.NestedModelAdmin):
    model = OccurrenceTenure
    form = OccurrenceTenureAdminForm

    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        "status",
                        "occurrence",
                        "significant_to_occurrence",
                        "purpose",
                        "comments",
                    ),
                )
            },
        ),
        (
            "Cadastre Spatial Identification",
            {
                "fields": (
                    ("tenure_area_id",),
                    (
                        "typename",
                        "featureid",
                    ),
                    ("tenure_area"),
                )
            },
        ),
        (
            "Cadastre Owner Information",
            {
                "fields": (
                    (
                        "owner_name",
                        "owner_count",
                    ),
                )
            },
        ),
        (
            "Occurrence Geometry",
            {
                "fields": (
                    "occurrence_geometry",
                    "geometry",
                )
            },
        ),
    )

    readonly_fields = ["typename", "featureid", "tenure_area", "geometry", "occurrence"]
    list_filter = ("status", "significant_to_occurrence", "purpose")

    def occurrence(self, obj):
        if obj.status == obj.STATUS_HISTORICAL:
            return f"{obj.occurrence.__str__()} [Historical]"
        return obj.occurrence

    def geometry(self, obj):
        if obj.status == obj.STATUS_HISTORICAL:
            geom = wkb_to_geojson(obj.historical_occurrence_geometry_ewkb)
            geom["properties"]["status"] = obj.STATUS_HISTORICAL
            geom["properties"]["occurrence_id"] = obj.occurrence.id
            return geom
        return obj.occurrence_geometry

    def tenure_area(self, obj):
        if obj.tenure_area_ewkb is None:
            return None
        return wkb_to_geojson(obj.tenure_area_ewkb)


@admin.register(OccurrenceTenurePurpose)
class OccurrenceTenurePurposeAdmin(
    CsvExportMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    pass


@admin.register(OccurrenceTenureVesting)
class OccurrenceTenureVestingAdmin(admin.ModelAdmin):
    pass


class PermitTypeAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ("group_type", "move_up_down_links", "name")
    list_filter = ("group_type", "archived")
    search_fields = ("name",)
    ordering = (
        "group_type",
        "order",
    )


class DatumAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ("srid", "move_up_down_links", "name")
    search_fields = ("srid",)
    ordering = ("order",)


class WildStatusAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class CoordinateSourceAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SoilTypeAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SoilConditionAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SoilColourAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SiteTypeAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SecondarySignAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    search_fields = ["name"]
    ordering = ("order",)


class SampleTypeAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ("group_type", "name", "move_up_down_links")
    list_filter = ("group_type", "archived")
    search_fields = ("name",)
    ordering = (
        "group_type",
        "order",
    )


class SampleDestinationAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class RockTypeAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class ReproductiveStateAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class LandFormAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class PrimaryDetectionMethodAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class PlantCountMethodAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class PlantCountAccuracyAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class PlantConditionAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class ObservationMethodAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class LocationAccuracyAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class IntensityAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class IdentificationCertaintyAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class DrainageAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class DeathReasonAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class CountedSubjectAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


class OccurrenceReportBulkImportTaskAdmin(DeleteProtectedModelAdmin):
    list_display = ["id", "datetime_queued", "processing_status"]
    list_filter = ["processing_status", "datetime_completed"]
    readonly_fields = ["datetime_queued"]


class OccurrenceReportBulkImportSchemaColumnInline(admin.StackedInline):
    model = OccurrenceReportBulkImportSchemaColumn
    extra = 0


class OccurrenceReportBulkImportSchemaAdmin(DeleteProtectedModelAdmin):
    list_display = ["group_type", "version", "datetime_created", "datetime_updated"]
    readonly_fields = ["datetime_created", "datetime_updated"]
    list_filter = ["group_type"]
    inlines = [OccurrenceReportBulkImportSchemaColumnInline]
    ordering = ["group_type", "version"]


class ObserverRoleAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["item", "move_up_down_links", "archived"]
    list_filter = ["archived"]
    search_fields = ["item"]
    ordering = ("order",)


class ObserverCategoryAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["item", "move_up_down_links", "archived"]
    list_filter = ["archived"]
    search_fields = ["item"]
    ordering = ("order",)


class AnimalHealthAdmin(
    CsvExportMixin,
    ArchivableModelAdminMixin,
    OrderedModelAdmin,
    DeleteProtectedModelAdmin,
):
    list_display = ["name", "move_up_down_links"]
    list_filter = ["archived"]
    search_fields = ["name"]
    ordering = ("order",)


# Each of the following models will be available to Django Admin.
admin.site.register(LandForm, LandFormAdmin)
admin.site.register(RockType, RockTypeAdmin)
admin.site.register(SoilType, SoilTypeAdmin)
admin.site.register(SiteType, SiteTypeAdmin)
admin.site.register(SoilColour, SoilColourAdmin)
admin.site.register(SoilCondition, SoilConditionAdmin)
admin.site.register(Drainage, DrainageAdmin)
admin.site.register(Intensity, IntensityAdmin)
admin.site.register(ObserverRole, ObserverRoleAdmin)
admin.site.register(ObserverCategory, ObserverCategoryAdmin)
admin.site.register(ObservationMethod, ObservationMethodAdmin)
admin.site.register(PlantCountMethod, PlantCountMethodAdmin)
admin.site.register(PlantCountAccuracy, PlantCountAccuracyAdmin)
admin.site.register(CountedSubject, CountedSubjectAdmin)
admin.site.register(PlantCondition, PlantConditionAdmin)
admin.site.register(PrimaryDetectionMethod, PrimaryDetectionMethodAdmin)
admin.site.register(SecondarySign, SecondarySignAdmin)
admin.site.register(ReproductiveState, ReproductiveStateAdmin)
admin.site.register(DeathReason, DeathReasonAdmin)
admin.site.register(AnimalHealth, AnimalHealthAdmin)
admin.site.register(IdentificationCertainty, IdentificationCertaintyAdmin)
admin.site.register(SampleType, SampleTypeAdmin)
admin.site.register(SampleDestination, SampleDestinationAdmin)
admin.site.register(PermitType, PermitTypeAdmin)
admin.site.register(Datum, DatumAdmin)
admin.site.register(CoordinateSource, CoordinateSourceAdmin)
admin.site.register(LocationAccuracy, LocationAccuracyAdmin)
admin.site.register(WildStatus, WildStatusAdmin)
admin.site.register(OccurrenceSite)
admin.site.register(OccurrenceReportBulkImportTask, OccurrenceReportBulkImportTaskAdmin)
admin.site.register(
    OccurrenceReportBulkImportSchema, OccurrenceReportBulkImportSchemaAdmin
)
