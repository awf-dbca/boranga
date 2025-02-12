<template id="occurrence-flora-dashboard">
    <div>
        <CollapsibleFilters component_title="Filters" ref="collapsible_filters" @created="collapsible_component_mounted"
            class="mb-2">
            <div class="row">
                <div class="col-md-4">
                    <div class="form-group" id="occurrence_name_lookup_form_group_id">
                        <label for="occurrence_name_lookup">Name of Occurrence:</label>
                        <select id="occurrence_name_lookup" name="occurrence_name_lookup" ref="occurrence_name_lookup"
                            class="form-control" />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group" id="select_scientific_name_by_groupname_occ">
                        <label for="occ_scientific_name_lookup_by_groupname">Scientific Name:</label>
                        <select id="occ_scientific_name_lookup_by_groupname"
                            name="occ_scientific_name_lookup_by_groupname" ref="occ_scientific_name_lookup_by_groupname"
                            class="form-control" />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group" id="select_status">
                        <label for="">Status:</label>
                        <select class="form-select" v-model="filterOCCFloraStatus">
                            <option value="all">All</option>
                            <option v-for="status in proposal_status" :value="status.value">{{ status.name }}</option>
                        </select>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div v-if="show_add_button" class="col-md-12">
            <div class="text-end">
                <button type="button" class="btn btn-primary mb-2 " @click.prevent="createFloraOccurrence"><i
                        class="fa-solid fa-circle-plus"></i> Add Flora Occurrence</button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable ref="flora_occ_datatable" :id="datatable_id" :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers" />
            </div>
        </div>
        <div v-if="occurrenceHistoryId">
            <OccurrenceHistory ref="occurrence_history" :key="occurrenceHistoryId"
                :occurrence-id="occurrenceHistoryId" />
        </div>
    </div>
</template>
<script>

import "babel-polyfill"
import datatable from '@/utils/vue/datatable.vue'
import CollapsibleFilters from '@/components/forms/collapsible_component.vue'
import FormSection from '@/components/forms/section_toggle.vue'
import OccurrenceHistory from '../internal/occurrence/species_occurrence_history.vue';
import Vue from 'vue'

import {
    api_endpoints,
    constants,
    helpers
} from '@/utils/hooks'
export default {
    name: 'OccurrenceFloraDashboard',
    props: {
        level: {
            type: String,
            required: true,
            validator: function (val) {
                let options = ['internal', 'external'];
                return options.indexOf(val) != -1 ? true : false;
            }
        },
        group_type_name: {
            type: String,
            required: true
        },
        group_type_id: {
            type: Number,
            required: true,
            default: 0
        },
        url: {
            type: String,
            required: true
        },
        profile: {
            type: Object,
            default: null
        },
        // for adding agendaitems for the meeting_obj.id
        meeting_obj: {
            type: Object,
            required: false
        },
        filterOCCFloraOccurrenceName_cache: {
            type: String,
            required: false,
            default: 'filterOCCFloraOccurrenceName',
        },
        filterOCCFloraScientificName_cache: {
            type: String,
            required: false,
            default: 'filterOCCFloraScientificName',
        },
        filterOCCFloraStatus_cache: {
            type: String,
            required: false,
            default: 'filterOCCFloraStatus',
        },
        filterOCCFromFloraDueDate_cache: {
            type: String,
            required: false,
            default: 'filterOCCFromFloraDueDate',
        },
        filterOCCToFloraDueDate_cache: {
            type: String,
            required: false,
            default: 'filterOCCToFloraDueDate',
        },
    },
    data() {
        let vm = this;
        return {
            uuid: 0,
            occurrenceHistoryId: null,
            datatable_id: 'occurrence-flora-datatable-' + vm._uid,

            // selected values for filtering
            filterOCCFloraOccurrenceName: sessionStorage.getItem(this.filterOCCFloraOccurrenceName_cache) ?
                sessionStorage.getItem(this.filterOCCFloraOccurrenceName_cache) : 'all',

            filterOCCFloraScientificName: sessionStorage.getItem(this.filterOCCFloraScientificName_cache) ?
                sessionStorage.getItem(this.filterOCCFloraScientificName_cache) : 'all',

            filterOCCFloraStatus: sessionStorage.getItem(this.filterOCCFloraStatus_cache) ?
                sessionStorage.getItem(this.filterOCCFloraStatus_cache) : 'all',

            filterOCCFromFloraDueDate: sessionStorage.getItem(this.filterOCCFromFloraDueDate_cache) ?
                sessionStorage.getItem(this.filterOCCFromFloraDueDate_cache) : '',
            filterOCCToFloraDueDate: sessionStorage.getItem(this.filterOCCToFloraDueDate_cache) ?
                sessionStorage.getItem(this.filterOCCToFloraDueDate_cache) : '',

            filterListsSpecies: {},
            occurrence_list: [],
            scientific_name_list: [],
            status_list: [],
            submissions_from_list: [],
            submissions_to_list: [],

            // filtering options
            internal_status: [
                { value: 'draft', name: 'Draft' },
                { value: 'discarded', name: 'Discarded' },
                { value: 'active', name: 'Active' },
                { value: 'locked', name: 'Locked' },
                { value: 'historical', name: 'Historical' },
            ],

            proposal_status: [],
        }
    },
    components: {
        datatable,
        CollapsibleFilters,
        FormSection,
        OccurrenceHistory,
    },
    watch: {
        filterOCCFloraOccurrenceName: function () {
            let vm = this;
            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFloraOccurrenceName_cache, vm.filterOCCFloraOccurrenceName);
        },
        filterOCCFloraScientificName: function () {
            let vm = this;
            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFloraScientificName_cache, vm.filterOCCFloraScientificName);
        },
        filterOCCFloraStatus: function () {
            let vm = this;
            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFloraStatus_cache, vm.filterOCCFloraStatus);
        },
        filterApplied: function () {
            if (this.$refs.collapsible_filters) {
                // Collapsible component exists
                this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
            }
        },
        filterOCCFromFloraDueDate: function () {
            let vm = this;
            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFromFloraDueDate_cache, vm.filterOCCFromFloraDueDate);
        },
        filterOCCToFloraDueDate: function () {
            let vm = this;
            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCToFloraDueDate_cache, vm.filterOCCToFloraDueDate);
        },
    },
    computed: {
        show_add_button: function () {
            return this.profile && this.profile.groups.includes(constants.GROUPS.OCCURRENCE_APPROVERS);
        },
        filterApplied: function () {
            if (this.filterOCCFloraOccurrenceName === 'all' &&
                this.filterOCCFloraScientificName === 'all' &&
                this.filterOCCFloraStatus === 'all' &&
                this.filterOCCFromFloraDueDate === '' &&
                this.filterOCCToFloraDueDate === '') {
                return false
            } else {
                return true
            }
        },
        is_external: function () {
            return this.level == 'external';
        },
        is_internal: function () {
            return this.level == 'internal'
        },
        addFloraOCCVisibility: function () {
            let visibility = false;
            if (this.is_internal) {
                visibility = true;
            }
            return visibility;
        },
        datatable_headers: function () {
            if (this.is_internal) {
                return ['ID', 'Number', 'Name of Occurrrence', 'Scientific Name', 'Wild Status', 'Number of Reports', 'Migrated From ID', 'Review Due', 'Status', 'Action']
            }
        },
        column_id: function () {
            return {
                data: "id",
                orderable: true,
                searchable: false,
                visible: false,
            }
        },
        column_number: function () {
            return {
                data: "occurrence_number",
                orderable: true,
                searchable: true,
                visible: true,
                name: "occurrence_number"
            }
        },
        column_name: function () {
            return {
                data: "occurrence_name",
                orderable: true,
                searchable: true,
                visible: true,
                name: "occurrence_name",
                'render': function (data, type, full) {
                    if (full.occurrence_name) {
                        let value = full.occurrence_name;
                        let result = helpers.dtPopover(value, 30, 'hover');
                        return type == 'export' ? value : result;
                    }
                    return ''
                },
            }
        },
        column_scientific_name: function () {
            return {
                data: "scientific_name",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function (data, type, full) {
                    if (full.scientific_name) {
                        let value = full.scientific_name;
                        let result = helpers.dtPopover(value, 30, 'hover');
                        return type == 'export' ? value : result;
                    }
                    return ''
                },
                name: "species__taxonomy__scientific_name",
            }
        },
        column_wild_status: function () {
            return {
                data: "wild_status",
                orderable: true,
                searchable: true,
                visible: true,
                name: "wild_status__name",
            }
        },
        column_number_of_reports: function () {
            return {
                data: "number_of_reports",
                orderable: false,
                searchable: false,
            }
        },
        column_migrated_from_id: function () {
            return {
                data: "migrated_from_id",
                orderable: false,
                searchable: true,
            }
        },
        column_review_due_date: function () {
            return {
                data: "review_due_date",
                orderable: true,
                searchable: true,
                visible: true,
                name: "review_due_date",
            }
        },
        column_status: function () {
            return {
                data: "processing_status_display",
                orderable: true,
                searchable: true,
                visible: true,
                name: "processing_status",
            }
        },
        column_action: function () {
            let vm = this
            return {
                data: "id",
                orderable: false,
                searchable: false,
                visible: true,
                'render': function (data, type, full) {
                    let links = "";
                    if (vm.is_internal) {
                        if (full.can_user_edit) {
                            if (full.processing_status == 'discarded') {
                                links += `<a href='#' data-reinstate-occ-proposal='${full.id}'>Reinstate</a><br/>`;
                                return links;
                            } else {
                                links += `<a href='/internal/occurrence/${full.id}?group_type_name=${vm.group_type_name}&action=edit'>Edit</a><br/>`;
                                if (full.processing_status == 'draft') {
                                    links += `<a href='#' data-discard-occ-proposal='${full.id}'>Discard</a><br/>`;
                                }
                            }
                        } else {
                            links += `<a href='/internal/occurrence/${full.id}?group_type_name=${vm.group_type_name}&action=view'>View</a><br/>`;
                        }
                        links += `<a href='#' data-history-occurrence='${full.id}'>History</a><br>`;
                    }
                    return links;
                }
            }
        },
        datatable_options: function () {
            let vm = this

            let columns = []
            let search = null
            let buttons = [
                {
                    extend: 'excel',
                    title: 'Boranga OCC Flora Excel Export',
                    text: '<i class="fa-solid fa-download"></i> Excel',
                    className: 'btn btn-primary me-2 rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                },
                {
                    extend: 'csv',
                    title: 'Boranga OCC Flora CSV Export',
                    text: '<i class="fa-solid fa-download"></i> CSV',
                    className: 'btn btn-primary rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                }
            ]
            if (vm.is_internal) {
                columns = [
                    vm.column_id,
                    vm.column_number,
                    vm.column_name,
                    vm.column_scientific_name,
                    vm.column_wild_status,
                    vm.column_number_of_reports,
                    vm.column_migrated_from_id,
                    vm.column_review_due_date,
                    vm.column_status,
                    vm.column_action,
                ]
                search = true
            }

            return {
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML
                },
                order: [
                    [0, 'desc']
                ],
                lengthMenu: [[10, 25, 50, 100, 100000000], [10, 25, 50, 100, "All"]],
                responsive: true,
                serverSide: true,
                searching: search,
                //  to show the "workflow Status","Action" columns always in the last position
                columnDefs: [
                    { responsivePriority: 1, targets: 1 },
                    { responsivePriority: 3, targets: -1, className: 'no-export' },
                    { responsivePriority: 2, targets: -2 }
                ],
                ajax: {
                    "url": this.url,
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function (d) {
                        d.filter_group_type = vm.group_type_name;
                        d.filter_occurrence_name = vm.filterOCCFloraOccurrenceName;
                        d.filter_scientific_name = vm.filterOCCFloraScientificName;
                        d.filter_status = vm.filterOCCFloraStatus;
                        d.filter_from_due_date = vm.filterOCCFromFloraDueDate;
                        d.filter_to_due_date = vm.filterOCCToFloraDueDate;
                        d.is_internal = vm.is_internal;
                    }
                },
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                columns: columns,
                processing: true,
                drawCallback: function () {
                    helpers.enablePopovers();
                },
                initComplete: function () {
                    helpers.enablePopovers();
                },
            }
        }

    },
    methods: {
        historyDocument: function (id) {
            this.occurrenceHistoryId = parseInt(id);
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.occurrence_history.isModalOpen = true;
            });
        },
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
        },
        initialiseOccurrenceNameLookup: function () {
            let vm = this;
            $(vm.$refs.occurrence_name_lookup).select2({
                minimumInputLength: 2,
                dropdownParent: $("#occurrence_name_lookup_form_group_id"),
                theme: 'bootstrap-5',
                allowClear: true,
                placeholder: "Select Name of Occurrence",
                ajax: {
                    url: api_endpoints.occurrence_name_lookup,
                    dataType: 'json',
                    data: function (params) {
                        var query = {
                            term: params.term,
                            type: 'public',
                            group_type_id: vm.group_type_id,
                        }
                        return query;
                    },
                },
            }).
                on("select2:select", function (e) {
                    var selected = $(e.currentTarget);
                    let data = e.params.data.text;
                    vm.filterOCCFloraOccurrenceName = data;
                    sessionStorage.setItem("filterOCCFloraOccurrenceNameText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCCFloraOccurrenceName = 'all';
                    sessionStorage.setItem("filterOCCFloraOccurrenceNameText", '');
                }).
                on("select2:open", function (e) {
                    const searchField = $('[aria-controls="select2-occurrence_name_lookup-results"]')
                    searchField[0].focus();
                });
        },
        initialiseScientificNameLookup: function () {
            let vm = this;
            $(vm.$refs.occ_scientific_name_lookup_by_groupname).select2({
                minimumInputLength: 2,
                dropdownParent: $("#select_scientific_name_by_groupname_occ"),
                theme: 'bootstrap-5',
                allowClear: true,
                placeholder: "Select Scientific Name",
                ajax: {
                    url: api_endpoints.scientific_name_lookup,
                    dataType: 'json',
                    data: function (params) {
                        var query = {
                            term: params.term,
                            type: 'public',
                            group_type_id: vm.group_type_id,
                        }
                        return query;
                    },
                },
            }).
                on("select2:select", function (e) {
                    var selected = $(e.currentTarget);
                    let data = e.params.data.id;
                    vm.filterOCCFloraScientificName = data;
                    sessionStorage.setItem("filterOCCFloraScientificNameText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCCFloraScientificName = 'all';
                    sessionStorage.setItem("filterOCCFloraScientificNameText", '');
                }).
                on("select2:open", function (e) {
                    const searchField = $('[aria-controls="select2-occ_scientific_name_lookup_by_groupname-results"]')
                    searchField[0].focus();
                });
        },
        fetchFilterLists: function () {
            let vm = this;
            //large FilterList of Species Values object
            vm.$http.get(api_endpoints.filter_lists_species + '?group_type_name=' + vm.group_type_name).then((response) => {
                vm.filterListsSpecies = response.body;
                vm.occurrence_list = vm.filterListsSpecies.occurrence_list;
                vm.scientific_name_list = vm.filterListsSpecies.scientific_name_list;
                vm.status_list = vm.filterListsSpecies.status_list;
                vm.submissions_from_list = vm.filterListsSpecies.submissions_from_list;
                vm.submissions_to_list = vm.filterListsSpecies.submissions_to_list;
                // vm.filterConservationCategory();
                // vm.filterDistrict();
                vm.proposal_status = vm.internal_status.slice().sort((a, b) => {
                    return a.name.trim().localeCompare(b.name.trim());
                });
            }, (error) => {
                console.log(error);
            })
        },
        createFloraOccurrence: async function () {
            swal.fire({
                title: `Add ${this.group_type_name} Occurrence`,
                text: "Are you sure you want to add a new flora occurrence?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Add Occurrence',
                reverseButtons: true,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then(async (swalresult) => {
                if (swalresult.isConfirmed) {
                    let newFloraOCRId = null
                    try {
                        const createUrl = api_endpoints.occurrence;
                        let payload = new Object();
                        payload.group_type_id = this.group_type_id
                        payload.internal_application = true
                        let savedFloraOCR = await Vue.http.post(createUrl, payload);
                        if (savedFloraOCR) {
                            newFloraOCRId = savedFloraOCR.body.id;
                        }
                    }
                    catch (err) {
                        console.log(err);
                        if (this.is_internal) {
                            return err;
                        }
                    }
                    this.$router.push({
                        name: 'internal-occurrence-detail',
                        params: { occurrence_id: newFloraOCRId },
                    });
                }
            });
        },
        discardOCC: function (occurrence_id) {
            let vm = this;
            swal.fire({
                title: "Discard Occurrence",
                text: "Are you sure you want to discard this occurrence?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Discard Report',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
                reverseButtons: true,
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    vm.$http.patch(api_endpoints.discard_occ_proposal(occurrence_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Discarded',
                                text: 'The occurrence has been discarded',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            }, (error) => {
                console.log(error);
            });
        },
        reinstateOCC: function (occurrence_id) {
            let vm = this;
            swal.fire({
                title: "Reinstate Occurrence",
                text: "Are you sure you want to reinstate this occurrence?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Reinstate Report',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
                reverseButtons: true,
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    vm.$http.patch(api_endpoints.reinstate_occ_proposal(occurrence_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Reinstated',
                                text: 'The occurrence has been reinstated',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.flora_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            }, (error) => {
                console.log(error);
            });
        },
        addEventListeners: function () {
            let vm = this;
            // internal Discard listener
            vm.$refs.flora_occ_datatable.vmDataTable.on('click', 'a[data-discard-occ-proposal]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-discard-occ-proposal');
                vm.discardOCC(id);
            });
            vm.$refs.flora_occ_datatable.vmDataTable.on('click', 'a[data-reinstate-occ-proposal]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-reinstate-occ-proposal');
                vm.reinstateOCC(id);
            });
            vm.$refs.flora_occ_datatable.vmDataTable.on('click', 'a[data-history-occurrence]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-history-occurrence');
                vm.historyDocument(id);
            });
            vm.$refs.flora_occ_datatable.vmDataTable.on('childRow.dt', function (e, settings) {
                helpers.enablePopovers();
            });
        },
    },

    mounted: function () {
        this.fetchFilterLists();
        let vm = this;
        $('a[data-toggle="collapse"]').on('click', function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
            }, 100);
        });
        this.$nextTick(() => {
            vm.initialiseOccurrenceNameLookup();
            vm.initialiseScientificNameLookup();
            vm.addEventListeners();

            if (sessionStorage.getItem("filterOCCFloraOccurrenceName") != 'all' && sessionStorage.getItem("filterOCCFloraOccurrenceName") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCCFloraOccurrenceNameText"), vm.filterOCCFloraOccurrenceName, false, true);
                $('#occurrence_name_lookup').append(newOption);
            }
            if (sessionStorage.getItem("filterOCCFloraScientificName") != 'all' && sessionStorage.getItem("filterOCCFloraScientificName") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCCFloraScientificNameText"), vm.filterOCCFloraScientificName, false, true);
                $('#occ_scientific_name_lookup_by_groupname').append(newOption);
            }
        });
    }
}
</script>
