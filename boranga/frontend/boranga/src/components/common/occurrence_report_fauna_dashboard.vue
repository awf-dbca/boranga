<template id="species_fauna_ocr_dashboard">
    <div>
        <CollapsibleFilters component_title="Filters" ref="collapsible_filters" @created="collapsible_component_mounted"
            class="mb-2">
            <div class="row">
                <div class="col-md-4">
                    <div class="form-group" id="select_occurrence">
                        <label for="ocr_occurrence_lookup">Occurrence:</label>
                        <select id="ocr_occurrence_lookup" name="ocr_occurrence_lookup" ref="ocr_occurrence_lookup"
                            class="form-control" />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group" id="select_scientific_name_by_groupname">
                        <label for="ocr_scientific_name_lookup_by_groupname">Scientific Name:</label>
                        <select id="ocr_scientific_name_lookup_by_groupname"
                            name="ocr_scientific_name_lookup_by_groupname" ref="ocr_scientific_name_lookup_by_groupname"
                            class="form-control" />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group" id="select_status">
                        <label for="ocr_status_lookup">Status:</label>
                        <select class="form-select" v-model="filterOCRFaunaStatus">
                            <option value="all">All</option>
                            <option v-for="status in processing_statuses" :value="status.value">{{ status.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Observation Date Range:</label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="observation_from_date"
                            v-model="filterOCRFaunaObservationFromDate">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for=""></label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="observation_from_date"
                            v-model="filterOCRFaunaObservationToDate">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Submitted Date Range:</label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="submitted_from_date"
                            v-model="filterOCRFaunaSubmittedFromDate">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for=""></label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="submitted_from_date"
                            v-model="filterOCRFaunaSubmittedToDate">
                    </div>
                </div>
            </div>
        </CollapsibleFilters>
        <div v-if="addFaunaOCRVisibility" class="col-md-12">
            <div class="text-end">
                <a type="button" role="button" class="btn btn-primary mb-2 me-2" :href="`/internal/occurrence-report/bulk_import/?group_type=fauna`"><i
                    class="bi bi-download pe-2"></i>Bulk Import</a>
                <button type="button" class="btn btn-primary mb-2 " @click.prevent="createFaunaOccurrenceReport"><i
                        class="fa-solid fa-circle-plus"></i> Add Fauna Occurrence Report</button>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <datatable ref="fauna_ocr_datatable" :id="datatable_id" :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers" />
            </div>
            <div v-if="occurrenceReportHistoryId">
                <OccurrenceReportHistory ref="occurrence_report_history" :key="occurrenceReportHistoryId"
                    :occurrence-report-id="occurrenceReportHistoryId" />
            </div>
        </div>
    </div>
</template>
<script>

import "babel-polyfill"
import datatable from '@/utils/vue/datatable.vue'
import CollapsibleFilters from '@/components/forms/collapsible_component.vue'
import FormSection from '@/components/forms/section_toggle.vue'
import OccurrenceReportHistory from '../internal/occurrence/species_occurrence_report_history.vue';
import Vue from 'vue'

import {
    api_endpoints,
    constants,
    helpers
} from '@/utils/hooks'
export default {
    name: 'OccurrenceReportFaunaTable',
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
        filterOCRFaunaOccurrence_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaOccurrence',
        },
        filterOCRFaunaScientificName_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaScientificName',
        },
        filterOCRFaunaStatus_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaStatus',
        },
        filterOCRFaunaObservationFromDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaObservationFromDate',
        },
        filterOCRFaunaObservationToDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaObservationToDate',
        },
        filterOCRFaunaSubmittedFromDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaSubmittedFromDate',
        },
        filterOCRFaunaSubmittedToDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRFaunaSubmittedToDate',
        },
        filterOCRFromFaunaDueDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRFromFaunaDueDate',
        },
        filterOCRToFaunaDueDate_cache: {
            type: String,
            required: false,
            default: 'filterOCRToFaunaDueDate',
        },
    },
    data() {
        let vm = this;
        return {
            uuid: 0,
            occurrenceReportHistoryId: null,
            datatable_id: 'species_fauna_ocr-datatable-' + vm._uid,

            // selected values for filtering
            filterOCRFaunaOccurrence: sessionStorage.getItem(this.filterOCRFaunaOccurrence_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaOccurrence_cache) : 'all',

            filterOCRFaunaScientificName: sessionStorage.getItem(this.filterOCRFaunaScientificName_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaScientificName_cache) : 'all',

            filterOCRFaunaStatus: sessionStorage.getItem(this.filterOCRFaunaStatus_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaStatus_cache) : 'all',

            filterOCRFaunaObservationFromDate: sessionStorage.getItem(this.filterOCRFaunaObservationFromDate_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaObservationFromDate_cache) : '',

            filterOCRFaunaObservationToDate: sessionStorage.getItem(this.filterOCRFaunaObservationToDate_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaObservationToDate_cache) : '',

            filterOCRFaunaSubmittedFromDate: sessionStorage.getItem(this.filterOCRFaunaSubmittedFromDate_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaSubmittedFromDate_cache) : '',

            filterOCRFaunaSubmittedToDate: sessionStorage.getItem(this.filterOCRFaunaSubmittedToDate_cache) ?
                sessionStorage.getItem(this.filterOCRFaunaSubmittedToDate_cache) : '',

            filterOCRFromFaunaDueDate: sessionStorage.getItem(this.filterOCRFromFaunaDueDate_cache) ?
                sessionStorage.getItem(this.filterOCRFromFaunaDueDate_cache) : '',
            filterOCRToFaunaDueDate: sessionStorage.getItem(this.filterOCRToFaunaDueDate_cache) ?
                sessionStorage.getItem(this.filterOCRToFaunaDueDate_cache) : '',

            filterListsSpecies: {},
            occurrence_list: [],
            scientific_name_list: [],
            status_list: [],
            submissions_from_list: [],
            submissions_to_list: [],

            // filtering options
            processing_statuses: [
                { value: 'draft', name: 'Draft' },
                { value: 'discarded', name: 'Discarded' },
                { value: 'with_assessor', name: 'With Assessor' },
                { value: 'with_referral', name: 'With Referral' },
                { value: 'with_approver', name: 'With Approver' },
                { value: 'approved', name: 'Approved' },
                { value: 'declined', name: 'Declined' },
            ],
        }
    },
    components: {
        datatable,
        CollapsibleFilters,
        FormSection,
        OccurrenceReportHistory,
    },
    watch: {
        filterOCRFaunaOccurrence: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaOccurrence_cache, vm.filterOCRFaunaOccurrence);
        },
        filterOCRFaunaScientificName: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaScientificName_cache, vm.filterOCRFaunaScientificName);
        },
        filterOCRFaunaStatus: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaStatus_cache, vm.filterOCRFaunaStatus);
        },
        filterOCRFaunaObservationFromDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaObservationFromDate_cache, vm.filterOCRFaunaObservationFromDate);
        },
        filterOCRFaunaObservationToDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaObservationToDate_cache, vm.filterOCRFaunaObservationToDate);
        },
        filterOCRFaunaSubmittedFromDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaSubmittedFromDate_cache, vm.filterOCRFaunaSubmittedFromDate);
        },
        filterOCRFaunaSubmittedToDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFaunaSubmittedToDate_cache, vm.filterOCRFaunaSubmittedToDate);
        },
        filterOCRFromFaunaDueDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRFromFaunaDueDate_cache, vm.filterOCRFromFaunaDueDate);
        },
        filterOCRToFaunaDueDate: function () {
            let vm = this;
            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCRToFaunaDueDate_cache, vm.filterOCRToFaunaDueDate);
        },
        filterApplied: function () {
            if (this.$refs.collapsible_filters) {
                // Collapsible component exists
                this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
            }
        },
    },
    computed: {
        filterApplied: function () {
            if (this.filterOCRFaunaOccurrence === 'all' &&
                this.filterOCRFaunaScientificName === 'all' &&
                this.filterOCRFaunaStatus === 'all' &&
                this.filterOCRFaunaObservationFromDate === '' &&
                this.filterOCRFaunaObservationToDate === '' &&
                this.filterOCRFaunaSubmittedFromDate === '' &&
                this.filterOCRFaunaSubmittedToDate === '' &&
                this.filterOCRFromFaunaDueDate === '' &&
                this.filterOCRToFaunaDueDate === '') {
                return false
            } else {
                return true
            }
        },
        addFaunaOCRVisibility: function () {
            return this.profile && this.profile.groups.includes(constants.GROUPS.INTERNAL_CONTRIBUTORS);
        },
        datatable_headers: function () {
            return ['ID', 'Number', 'Occurrence', 'Scientific Name', 'Observation Date', 'Main Observer', 'Migrated From ID', 'Submitted on', 'Submitter', 'Status', 'Action']
        },
        column_id: function () {
            return {
                data: "id",
                orderable: true,
                searchable: false,
                visible: false,
                name: "id",
            }
        },
        column_number: function () {
            let vm = this;
            return {
                data: "occurrence_report_number",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function (data, type, full) {
                    let value = full.occurrence_report_number
                    if (full.is_new_contributor) {
                        value += ' <span class="badge bg-warning">New Contributor</span>'
                    }
                    return value
                },
                name: "id",
            }
        },
        column_occurrence: function () {
            return {
                data: "occurrence_name",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function (data, type, full) {
                    if (full.occurrence_name) {
                        return full.occurrence_name;
                    }
                    return 'NOT SET'
                },
                name: "occurrence__occurrence_number",
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
        column_observation_date_time: function () {
            return {
                data: "observation_date",
                orderable: true,
                searchable: true,
                visible: true,
                name: "observation_date",
            }
        },
        column_main_observer: function () {
            return {
                data: "main_observer",
                orderable: false,
                searchable: false,
                visible: true,
                name: "main_observer",
                render: function (data, type, full) {
                    return full.main_observer;
                }
            }
        },
        column_migrated_from_id: function () {
            return {
                data: "migrated_from_id",
                orderable: false,
                searchable: true,
            }
        },
        column_lodgement_date: function () {
            return {
                data: "lodgement_date",
                orderable: true,
                searchable: true,
                visible: true,
                name: "lodgement_date",
            }
        },
        column_submitter: function () {
            return {
                data: "submitter",
                orderable: false,
                searchable: false,
                visible: true,
                name: "submitter__first_name, submitter__last_name",
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
                    if (full.internal_user_edit) {
                        if (full.processing_status == 'discarded') {
                            links += `<a href='#${full.id}' data-reinstate-ocr-proposal='${full.id}'>Reinstate</a><br/>`;
                        } else {
                            links += `<a href='/internal/occurrence-report/${full.id}?action=edit'>Continue</a><br/>`;
                            links += `<a href='#${full.id}' data-discard-ocr-proposal='${full.id}'>Discard</a><br/>`;
                            links += `<a href='#' data-history-occurrence-report='${full.id}'>History</a><br>`;
                        }
                    }
                    else {
                        if (full.can_user_assess || full.can_user_approve) {
                            links += `<a href='/internal/occurrence-report/${full.id}?action=edit'>Process</a><br/>`;
                        }
                        else {
                            links += `<a href='/internal/occurrence-report/${full.id}?action=view'>View</a><br/>`;
                        }
                        links += `<a href='#' data-history-occurrence-report='${full.id}'>History</a><br>`;
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
                    title: 'Boranga OCR Fauna Excel Export',
                    text: '<i class="fa-solid fa-download"></i> Excel',
                    className: 'btn btn-primary me-2 rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                },
                {
                    extend: 'csv',
                    title: 'Boranga OCR Fauna CSV Export',
                    text: '<i class="fa-solid fa-download"></i> CSV',
                    className: 'btn btn-primary rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                }
            ]
            columns = [
                vm.column_id,
                vm.column_number,
                vm.column_occurrence,
                vm.column_scientific_name,
                vm.column_observation_date_time,
                vm.column_main_observer,
                vm.column_migrated_from_id,
                vm.column_lodgement_date,
                vm.column_submitter,
                vm.column_status,
                vm.column_action,
            ]
            search = true

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
                        d.filter_occurrence = vm.filterOCRFaunaOccurrence;
                        d.filter_scientific_name = vm.filterOCRFaunaScientificName;
                        d.filter_status = vm.filterOCRFaunaStatus;
                        d.filter_observation_from_date = vm.filterOCRFaunaObservationFromDate;
                        d.filter_observation_to_date = vm.filterOCRFaunaObservationToDate;
                        d.filter_submitted_from_date = vm.filterOCRFaunaSubmittedFromDate;
                        d.filter_submitted_to_date = vm.filterOCRFaunaSubmittedToDate;
                        d.filter_from_due_date = vm.filterOCRFromFaunaDueDate;
                        d.filter_to_due_date = vm.filterOCRToFaunaDueDate;
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
            this.occurrenceReportHistoryId = parseInt(id);
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.occurrence_report_history.isModalOpen = true;
            });
        },
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
        },
        initialiseOccurrenceLookup: function () {
            let vm = this;
            $(vm.$refs.ocr_occurrence_lookup).select2({
                minimumInputLength: 2,
                dropdownParent: $("#select_occurrence"),
                "theme": "bootstrap-5",
                allowClear: true,
                placeholder: "Select Occurrence",
                ajax: {
                    url: api_endpoints.species_lookup,
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
                    vm.filterOCRFaunaOccurrence = data;
                    sessionStorage.setItem("filterOCRFaunaOccurrenceText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCRFaunaOccurrence = 'all';
                    sessionStorage.setItem("filterOCRFaunaOccurrenceText", '');
                }).
                on("select2:open", function (e) {
                    const searchField = $('[aria-controls="select2-ocr_occurrence_lookup-results"]')
                    searchField[0].focus();
                });
        },
        initialiseScientificNameLookup: function () {
            let vm = this;
            $(vm.$refs.ocr_scientific_name_lookup_by_groupname).select2({
                minimumInputLength: 2,
                dropdownParent: $("#select_scientific_name_by_groupname"),
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
                    vm.filterOCRFaunaScientificName = data;
                    sessionStorage.setItem("filterOCRFaunaScientificNameText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCRFaunaScientificName = 'all';
                    sessionStorage.setItem("filterOCRFaunaScientificNameText", '');
                }).
                on("select2:open", function (e) {
                    const searchField = $('[aria-controls="select2-ocr_scientific_name_lookup_by_groupname-results"]')
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
            }, (error) => {
                console.log(error);
            })
        },
        createFaunaOccurrenceReport: async function () {
            swal.fire({
                title: `Add ${this.group_type_name} Occurrence Report`,
                text: "Are you sure you want to add a new occurrence report?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Add Occurrence Report',
                reverseButtons: true,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary'
                },
            }).then(async (swalresult) => {
                if (swalresult.isConfirmed) {
                    let newFaunaOCRId = null
                    try {
                        const createUrl = api_endpoints.occurrence_report + "/";
                        let payload = new Object();
                        payload.group_type_id = this.group_type_id
                        payload.internal_application = true
                        let savedFaunaOCR = await Vue.http.post(createUrl, payload);
                        if (savedFaunaOCR) {
                            newFaunaOCRId = savedFaunaOCR.body.id;
                        }
                    }
                    catch (err) {
                        console.log(err);
                    }
                    this.$router.push({
                        name: 'internal-occurrence-report-detail',
                        params: { occurrence_report_id: newFaunaOCRId },
                    });
                }
            });
        },
        discardOCRProposal: function (occurrence_report_id) {
            let vm = this;
            swal.fire({
                title: "Discard Report",
                text: "Are you sure you want to discard this report?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Discard Report',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary'
                },
                reverseButtons: true,
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    vm.$http.patch(api_endpoints.discard_ocr_proposal(occurrence_report_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Discarded',
                                text: 'Your report has been discarded',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            }, (error) => {
                console.log(error);
            });
        },
        reinstateOCRProposal: function (occurrence_report_id) {
            let vm = this;
            swal.fire({
                title: "Reinstate Report",
                text: "Are you sure you want to reinstate this report?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Reinstate Report',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary'
                },
                reverseButtons: true,
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    vm.$http.patch(api_endpoints.reinstate_ocr_proposal(occurrence_report_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Reinstated',
                                text: 'Your report has been reinstated',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.fauna_ocr_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
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
            vm.$refs.fauna_ocr_datatable.vmDataTable.on('click', 'a[data-discard-ocr-proposal]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-discard-ocr-proposal');
                vm.discardOCRProposal(id);
            });
            vm.$refs.fauna_ocr_datatable.vmDataTable.on('click', 'a[data-reinstate-ocr-proposal]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-reinstate-ocr-proposal');
                vm.reinstateOCRProposal(id);
            });
            vm.$refs.fauna_ocr_datatable.vmDataTable.on('click', 'a[data-history-occurrence-report]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-history-occurrence-report');
                vm.historyDocument(id);
            });
            vm.$refs.fauna_ocr_datatable.vmDataTable.on('childRow.dt', function (e, settings) {
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
            vm.initialiseOccurrenceLookup();
            vm.initialiseScientificNameLookup();
            vm.addEventListeners();
            if (sessionStorage.getItem("filterOCRFaunaOccurrence") != 'all' && sessionStorage.getItem("filterOCRFaunaOccurrence") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCRFaunaOccurrenceText"), vm.filterOCRFaunaOccurrence, false, true);
                $('#ocr_occurrence_lookup').append(newOption);
            }
            if (sessionStorage.getItem("filterOCRFaunaScientificName") != 'all' && sessionStorage.getItem("filterOCRFaunaScientificName") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCRFaunaScientificNameText"), vm.filterOCRFaunaScientificName, false, true);
                $('#ocr_scientific_name_lookup').append(newOption);
            }
        });
    }
}
</script>
<style scoped>
.dt-buttons {
    float: right;
}

.collapse-icon {
    cursor: pointer;
}

.collapse-icon::before {
    top: 5px;
    left: 4px;
    height: 14px;
    width: 14px;
    border-radius: 14px;
    line-height: 14px;
    border: 2px solid white;
    line-height: 14px;
    content: '-';
    color: white;
    background-color: #d33333;
    display: inline-block;
    box-shadow: 0px 0px 3px #444;
    box-sizing: content-box;
    text-align: center;
    text-indent: 0 !important;
    font-family: 'Courier New', Courier monospace;
    margin: 5px;
}

.expand-icon {
    cursor: pointer;
}

.expand-icon::before {
    top: 5px;
    left: 4px;
    height: 14px;
    width: 14px;
    border-radius: 14px;
    line-height: 14px;
    border: 2px solid white;
    line-height: 14px;
    content: '+';
    color: white;
    background-color: #337ab7;
    display: inline-block;
    box-shadow: 0px 0px 3px #444;
    box-sizing: content-box;
    text-align: center;
    text-indent: 0 !important;
    font-family: 'Courier New', Courier monospace;
    margin: 5px;
}
</style>
