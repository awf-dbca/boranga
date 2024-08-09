import nested_admin
from django.contrib.gis import admin, forms

from boranga.admin import ArchivableModelAdminMixin, DeleteProtectedModelAdmin
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
    OccurrenceGeometry,
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
                        "intersects",
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
                    (
                        "intersects",
                        "locked",
                    ),
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
    ArchivableModelAdminMixin, DeleteProtectedModelAdmin
):
    pass


@admin.register(OccurrenceTenureVesting)
class OccurrenceTenureVestingAdmin(admin.ModelAdmin):
    pass


class PermitTypeAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ("group_type", "name")
    list_filter = ("group_type",)


class DatumAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ("srid", "name")
    search_fields = ("srid", "name")


class WildStatusAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class CoordinateSourceAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SoilTypeAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SoilConditionAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SoilColourAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SiteTypeAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SecondarySignAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class SampleTypeAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ("group_type", "name")
    list_filter = ("group_type",)


class SampleDestinationAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class RockTypeAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class ReproductiveStateAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class LandFormAdmin(DeleteProtectedModelAdmin):
    list_display = ["name"]
    fields = ["name"]  # Not showing the archived field for now as requires
    # more work on the frontend due to django-multiselectfield


class PrimaryDetectionMethodAdmin(DeleteProtectedModelAdmin):
    list_display = ["name"]
    fields = ["name"]  # Not showing the archived field for now as requires
    # more work on the frontend due to django-multiselectfield


class PlantCountMethodAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class PlantCountAccuracyAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class PlantConditionAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class ObservationMethodAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class LocationAccuracyAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class IntensityAdmin(ArchivableModelAdminMixin, DeleteProtectedModelAdmin):
    list_display = ["name"]


class IdentificationCertaintyAdmin(
    ArchivableModelAdminMixin, DeleteProtectedModelAdmin
):
    list_display = ["name"]


# Each of the following models will be available to Django Admin.
admin.site.register(LandForm, LandFormAdmin)
admin.site.register(RockType, RockTypeAdmin)
admin.site.register(SoilType, SoilTypeAdmin)
admin.site.register(SiteType, SiteTypeAdmin)
admin.site.register(SoilColour, SoilColourAdmin)
admin.site.register(SoilCondition, SoilConditionAdmin)
admin.site.register(Drainage, DeleteProtectedModelAdmin)
admin.site.register(Intensity, IntensityAdmin)
admin.site.register(ObservationMethod, ObservationMethodAdmin)
admin.site.register(PlantCountMethod, PlantCountMethodAdmin)
admin.site.register(PlantCountAccuracy, PlantCountAccuracyAdmin)
admin.site.register(CountedSubject, DeleteProtectedModelAdmin)
admin.site.register(PlantCondition, PlantConditionAdmin)
admin.site.register(PrimaryDetectionMethod, PrimaryDetectionMethodAdmin)
admin.site.register(SecondarySign, SecondarySignAdmin)
admin.site.register(ReproductiveState, ReproductiveStateAdmin)
admin.site.register(DeathReason, DeleteProtectedModelAdmin)
admin.site.register(AnimalHealth, DeleteProtectedModelAdmin)
admin.site.register(IdentificationCertainty, IdentificationCertaintyAdmin)
admin.site.register(SampleType, SampleTypeAdmin)
admin.site.register(SampleDestination, SampleDestinationAdmin)
admin.site.register(PermitType, PermitTypeAdmin)
admin.site.register(Datum, DatumAdmin)
admin.site.register(CoordinateSource, CoordinateSourceAdmin)
admin.site.register(LocationAccuracy, LocationAccuracyAdmin)
admin.site.register(WildStatus, WildStatusAdmin)
admin.site.register(OccurrenceSite)
