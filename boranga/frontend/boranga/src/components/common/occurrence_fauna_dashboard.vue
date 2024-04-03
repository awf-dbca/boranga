<template id="occurrence-fauna-dashboard">
    <div>
        <CollapsibleFilters component_title="Filters" ref="collapsible_filters" @created="collapsible_component_mounted"
            class="mb-2">
            <div class="row">
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
                        <select class="form-select" v-model="filterOCCFaunaStatus">
                            <option value="all">All</option>
                            <option v-for="status in proposal_status" :value="status.value">{{ status.name }}</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Submitted From Date:</label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="submitted_from_date"
                            v-model="filterOCCFaunaSubmittedFromDate">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Submitted To Date:</label>
                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="submitted_from_date"
                            v-model="filterOCCFaunaSubmittedToDate">
                    </div>
                </div>
            </div>
        </CollapsibleFilters>
        <div class="row">
            <div class="col-lg-12">
                <datatable ref="fauna_occ_datatable" :id="datatable_id" :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers" />
            </div>
        </div>
    </div>
</template>
<script>

import "babel-polyfill"
import datatable from '@/utils/vue/datatable.vue'
import CollapsibleFilters from '@/components/forms/collapsible_component.vue'
import FormSection from '@/components/forms/section_toggle.vue'
import Vue from 'vue'

import {
    api_endpoints,
    constants,
    helpers
} from '@/utils/hooks'
export default {
    name: 'OccurrenceFaunaDashboard',
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
        // for adding agendaitems for the meeting_obj.id
        meeting_obj: {
            type: Object,
            required: false
        },
        filterOCCFaunaOccurrence_cache: {
            type: String,
            required: false,
            default: 'filterOCCFaunaOccurrence',
        },
        filterOCCFaunaScientificName_cache: {
            type: String,
            required: false,
            default: 'filterOCCFaunaScientificName',
        },
        filterOCCFaunaStatus_cache: {
            type: String,
            required: false,
            default: 'filterOCCFaunaStatus',
        },
        filterOCCFaunaSubmittedFromDate_cache: {
            type: String,
            required: false,
            default: 'filterOCCFaunaSubmittedFromDate',
        },
        filterOCCFaunaSubmittedToDate_cache: {
            type: String,
            required: false,
            default: 'filterOCCFaunaSubmittedToDate',
        },

    },
    data() {
        let vm = this;
        return {
            datatable_id: 'occurrence-fauna-datatable-' + vm._uid,

            //Profile to check if user has access to process Proposal
            profile: {},
            is_payment_admin: false,

            // selected values for filtering
            filterOCCFaunaOccurrence: sessionStorage.getItem(this.filterOCCFaunaOccurrence_cache) ?
                sessionStorage.getItem(this.filterOCCFaunaOccurrence_cache) : 'all',

            filterOCCFaunaScientificName: sessionStorage.getItem(this.filterOCCFaunaScientificName_cache) ?
                sessionStorage.getItem(this.filterOCCFaunaScientificName_cache) : 'all',

            filterOCCFaunaStatus: sessionStorage.getItem(this.filterOCCFaunaStatus_cache) ?
                sessionStorage.getItem(this.filterOCCFaunaStatus_cache) : 'all',

            filterOCCFaunaSubmittedFromDate: sessionStorage.getItem(this.filterOCCFaunaSubmittedFromDate_cache) ?
                sessionStorage.getItem(this.filterOCCFaunaSubmittedFromDate_cache) : '',

            filterOCCFaunaSubmittedToDate: sessionStorage.getItem(this.filterOCCFaunaSubmittedToDate_cache) ?
                sessionStorage.getItem(this.filterOCCFaunaSubmittedToDate_cache) : '',

            filterListsSpecies: {},
            occurrence_list: [],
            scientific_name_list: [],
            status_list: [],
            submissions_from_list: [],
            submissions_to_list: [],

            // filtering options
            internal_status: [
                { value: 'draft', name: 'Draft' },
                { value: 'locked', name: 'Locked' },
                { value: 'split', name: 'Split' },
                { value: 'combine', name: 'Combine' },
                { value: 'historical', name: 'Historical' },
            ],

            proposal_status: [],
        }
    },
    components: {
        datatable,
        CollapsibleFilters,
        FormSection,
    },
    watch: {
        filterOCCFaunaOccurrence: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFaunaOccurrence_cache, vm.filterOCCFaunaOccurrence);
        },
        filterOCCFaunaScientificName: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFaunaScientificName_cache, vm.filterOCCFaunaScientificName);
        },
        filterOCCFaunaStatus: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call. 
            sessionStorage.setItem(vm.filterOCCFaunaStatus_cache, vm.filterOCCFaunaStatus);
        },
        filterOCCFaunaSubmittedFromDate: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFaunaSubmittedFromDate_cache, vm.filterOCCFaunaSubmittedFromDate);
        },
        filterOCCFaunaSubmittedToDate: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterOCCFaunaSubmittedToDate_cache, vm.filterOCCFaunaSubmittedToDate);
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
            if (this.filterOCCFaunaOccurrence === 'all' &&
                this.filterOCCFaunaScientificName === 'all' &&
                this.filterOCCFaunaStatus === 'all' &&
                this.filterOCCFaunaSubmittedFromDate === '' &&
                this.filterOCCFaunaSubmittedToDate === '') {
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
        addFaunaOCCVisibility: function () {
            let visibility = false;
            if (this.is_internal) {
                visibility = true;
            }
            return visibility;
        },
        datatable_headers: function () {
            if (this.is_internal) {
                return ['Number', 'Scientific Name', 'Number of Reports', 'Status', 'Action']
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
            }
        },
        column_scientific_name: function () {
            return {
                data: "scientific_name",
                orderable: true,
                searchable: true,
                visible: true,
                name: "species__taxonomy__scientific_name",
            }
        },
        column_number_of_reports: function () {
            return {
                data: "number_of_reports",
                orderable: false,
                searchable: false,
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
                    if (!vm.is_external) {
                        if (full.internal_user_edit) {
                            links += `<a href='/internal/occurrence/${full.id}'>Continue</a><br/>`;
                            links += `<a href='#${full.id}' data-discard-occ-proposal='${full.id}'>Discard</a><br/>`;
                        }
                        else {
                            if (full.assessor_process) {
                                links += `<a href='/internal/occurrence/${full.id}'>Process</a><br/>`;
                            }
                            else {
                                if (full.assessor_edit) {
                                    links += `<a href='/internal/occurrence/${full.id}?group_type_name=${vm.group_type_name}&action=edit'>Edit</a><br/>`;
                                }
                                links += `<a href='/internal/occurrence/${full.id}?group_type_name=${vm.group_type_name}&action=view'>View</a><br/>`;
                            }
                        }
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
                    text: '<i class="fa-solid fa-download"></i> Excel',
                    className: 'btn btn-primary me-2 rounded',
                    action: function (e, dt, node, config) {
                        vm.exportData("excel");
                    }
                },
                {
                    text: '<i class="fa-solid fa-download"></i> CSV',
                    className: 'btn btn-primary rounded',
                    action: function (e, dt, node, config) {
                        vm.exportData("csv");
                    }
                }
            ]
            if (vm.is_internal) {
                columns = [
                    vm.column_number,
                    vm.column_scientific_name,
                    vm.column_number_of_reports,
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
                lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                responsive: true,
                serverSide: true,
                searching: search,
                //  to show the "workflow Status","Action" columns always in the last position
                columnDefs: [
                    { responsivePriority: 1, targets: 0 },
                    { responsivePriority: 3, targets: -1 },
                    { responsivePriority: 2, targets: -2 }
                ],
                ajax: {
                    "url": this.url,
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function (d) {
                        d.filter_group_type = vm.group_type_name;
                        d.filter_occurrence = vm.filterOCCFaunaOccurrence;
                        d.filter_scientific_name = vm.filterOCCFaunaScientificName;
                        d.filter_status = vm.filterOCCFaunaStatus;
                        d.filter_submitted_from_date = vm.filterOCCFaunaSubmittedFromDate;
                        d.filter_submitted_to_date = vm.filterOCCFaunaSubmittedToDate;
                        d.is_internal = vm.is_internal;
                    }
                },
                //dom: 'lBfrtip',
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,

                columns: columns,
                processing: true,
                initComplete: function () {
                    helpers.enablePopovers();
                },
            }
        }

    },
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
        },
        initialiseOccurrenceLookup: function () {
            let vm = this;
            $(vm.$refs.occ_occurrence_lookup).select2({
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
                    vm.filterOCCFaunaOccurrence = data;
                    sessionStorage.setItem("filterOCCFaunaOccurrenceText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCCFaunaOccurrence = 'all';
                    sessionStorage.setItem("filterOCCFaunaOccurrenceText", '');
                }).
                on("select2:open", function (e) {
                    const searchField = $('[aria-controls="select2-occ_occurrence_lookup-results"]')
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
                    vm.filterOCCFaunaScientificName = data;
                    sessionStorage.setItem("filterOCCFaunaScientificNameText", e.params.data.text);
                }).
                on("select2:unselect", function (e) {
                    var selected = $(e.currentTarget);
                    vm.filterOCCFaunaScientificName = 'all';
                    sessionStorage.setItem("filterOCCFaunaScientificNameText", '');
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
        createFaunaOccurrence: async function () {
            let newFaunaOCRId = null
            try {
                const createUrl = api_endpoints.occurrence + "/";
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
                if (this.is_internal) {
                    return err;
                }
            }
            this.$router.push({
                name: 'internal-occurrence',
                params: { occurrence_id: newFaunaOCRId },
            });
        },
        discardOCRProposal: function (occurrence_id) {
            let vm = this;
            swal.fire({
                title: "Discard Report",
                text: "Are you sure you want to discard this report?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Discard Report',
                confirmButtonColor: '#d9534f'
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    vm.$http.delete(api_endpoints.discard_occ_proposal(occurrence_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Discarded',
                                text: 'Your report has been discarded',
                                icon: 'success',
                                confirmButtonColor: '#226fbb',
                            });
                            vm.$refs.fauna_occ_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            }, (error) => {

            });
        },
        addEventListeners: function () {
            let vm = this;
            // internal Discard listener
            vm.$refs.fauna_occ_datatable.vmDataTable.on('click', 'a[data-discard-occ-proposal]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-discard-occ-proposal');
                vm.discardOCRProposal(id);
            });
        },
        initialiseSearch: function () {
            this.submitterSearch();
        },
        submitterSearch: function () {
            let vm = this;
            vm.$refs.fauna_occ_datatable.table.dataTableExt.afnFiltering.push(
                function (settings, data, dataIndex, original) {
                    let filtered_submitter = vm.filterProposalSubmitter;
                    if (filtered_submitter == 'All') { return true; }
                    return filtered_submitter == original.submitter.email;
                }
            );
        },
        exportData: function (format) {
            let vm = this;
            const columns_new = {
                "0": {
                    "data": "occurrence",
                    "name": "occurrence__id, occurrence__occurrence_number",
                    "orderable": "true",
                    "search": {
                        "regex": "false",
                        "value": ""
                    },
                    "searchable": "false"
                },
                "1": {
                    "data": "species",
                    "name": "occurrence__species",
                    "orderable": "true",
                    "search": {
                        "regex": "false",
                        "value": ""
                    },
                    "searchable": "true"
                },
                "2": {
                    "data": "scientific_name",
                    "name": "occurrence__species__taxonomy__scientific_name",
                    "orderable": "true",
                    "search": {
                        "regex": "false",
                        "value": ""
                    },
                    "searchable": "true"
                },
                "3": {
                    "data": "reported_date",
                    "name": "occurrence__reported_date",
                    "searchable": "true",
                    "orderable": "true",
                    "search": {
                        "value": "",
                        "regex": "false"
                    }
                },
                "4": {
                    "data": "submitter",
                    "searchable": "true",
                    "orderable": "true",
                    "search": {
                        "value": "",
                        "regex": "false"
                    }
                },
                "5": {
                    "data": "processing_status",
                    "name": "occurrence__processing_status",
                    "searchable": "true",
                    "orderable": "true",
                    "search": {
                        "value": "",
                        "regex": "false"
                    }
                },
            };

            const object_load = {
                columns: columns_new,
                filter_group_type: vm.group_type_name,
                filter_occurrence: vm.filterOCCFaunaOccurrence,
                filter_scientific_name: vm.filterOCCFaunaScientificName,
                filter_status: vm.filterOCCFaunaStatus,
                filter_submitted_from_date: vm.filterOCCFaunaSubmittedFromDate,
                filter_submitted_to_date: vm.filterOCCFaunaSubmittedToDate,
                is_internal: vm.is_internal,
                export_format: format
            };

            const url = api_endpoints.occurrence_internal_export;
            const keyValuePairs = [];

            for (const key in object_load) {
                if (object_load.hasOwnProperty(key)) {
                    const encodedKey = encodeURIComponent(key);
                    let encodedValue = '';

                    if (typeof object_load[key] === 'object') {
                        encodedValue = encodeURIComponent(JSON.stringify(object_load[key]));
                    }
                    else {
                        encodedValue = encodeURIComponent(object_load[key]);
                    }
                    keyValuePairs.push(`${encodedKey}=${encodedValue}`);
                }
            }
            const params = keyValuePairs.join('&');
            const fullUrl = `${url}?${params}`;
            try {
                if (format === "excel") {
                    $.ajax({
                        type: "GET",
                        url: fullUrl,
                        contentType: "application/vnd.ms-excel",
                        dataType: "binary",
                        xhrFields: {
                            responseType: 'blob'
                        },

                        success: function (response, status, request) {
                            var contentDispositionHeader = request.getResponseHeader('Content-Disposition');
                            var filename = contentDispositionHeader.split('filename=')[1];
                            window.URL = window.URL || window.webkitURL;
                            var blob = new Blob([response], { type: "application/vnd.ms-excel" });

                            var downloadUrl = window.URL.createObjectURL(blob);
                            var a = document.createElement("a");
                            a.href = downloadUrl;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        },
                        error: function (xhr, status, error) {
                            console.log(error);
                        },
                    });
                }
                else if (format === "csv") {
                    $.ajax({
                        type: "GET",
                        url: fullUrl,
                        success: function (response, status, request) {
                            var contentDispositionHeader = request.getResponseHeader('Content-Disposition');
                            var filename = contentDispositionHeader.split('filename=')[1];
                            window.URL = window.URL || window.webkitURL;
                            var blob = new Blob([response], { type: "text/csv" });

                            var downloadUrl = window.URL.createObjectURL(blob);
                            var a = document.createElement("a");
                            a.href = downloadUrl;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        },
                        error: function (xhr, status, error) {
                            console.log(error);
                        },
                    });
                }
            }
            catch (err) {
                console.log(err);
                if (vm.is_internal) {
                    return err;
                }
            }
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

            if (sessionStorage.getItem("filterOCCFaunaOccurrence") != 'all' && sessionStorage.getItem("filterOCCFaunaOccurrence") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCCFaunaOccurrenceText"), vm.filterOCCFaunaOccurrence, false, true);
                $('#occ_occurrence_lookup').append(newOption);
            }
            if (sessionStorage.getItem("filterOCCFaunaScientificName") != 'all' && sessionStorage.getItem("filterOCCFaunaScientificName") != null) {
                var newOption = new Option(sessionStorage.getItem("filterOCCFaunaScientificNameText"), vm.filterOCCFaunaScientificName, false, true);
                $('#occ_scientific_name_lookup_by_groupname').append(newOption);
            }
        });
    }
}
</script>