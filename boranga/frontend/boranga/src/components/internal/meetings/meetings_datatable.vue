<template id="meetings_datatable">
    <div>
        <CollapsibleFilters component_title="Filters" ref="collapsible_filters" @created="collapsible_component_mounted"
            class="mb-2">
            <div class="row">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Start Date Range:</label>
                        <input type="datetime-local" class="form-control" placeholder="DD/MM/YYYY" id="from_start_date"
                            v-model="filterFromMeetingStartDate">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for=""></label>
                        <input type="datetime-local" class="form-control" placeholder="DD/MM/YYYY" id="to_start_date"
                            v-model="filterToMeetingStartDate">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">End Date :</label>
                        <input type="datetime-local" class="form-control" placeholder="DD/MM/YYYY" id="from_end_date"
                            v-model="filterFromMeetingEndDate">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for=""></label>
                        <input type="datetime-local" class="form-control" placeholder="DD/MM/YYYY" id="to_end_date"
                            v-model="filterToMeetingEndDate">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Status:</label>
                        <select class="form-select" v-model="filterMeetingStatus">
                            <option value="all">All</option>
                            <option v-for="status in processing_statuses" :value="status.value">{{ status.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>
        <div v-if="profile && profile.groups.includes(constants.GROUPS.CONSERVATION_STATUS_APPROVERS)"
            class="col-md-12">
            <div class="text-end">
                <button type="button" class="btn btn-primary mb-2 " @click.prevent="createMeeting"><i
                        class="fa-solid fa-circle-plus"></i> Add Meeting</button>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <datatable ref="meetings_datatable" :id="datatable_id" :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers" />
            </div>
        </div>
    </div>
</template>
<script>
import {
    api_endpoints,
    constants,
    helpers
}
    from '@/utils/hooks'
import "babel-polyfill"
import datatable from '@/utils/vue/datatable.vue'
import CollapsibleFilters from '@/components/forms/collapsible_component.vue'
import moment from 'moment'
import Vue from 'vue'

export default {
    name: 'MeetingsDatatable',
    props: {
        url: {
            type: String,
            required: true
        },
        filterFromMeetingStartDate_cache: {
            type: String,
            required: false,
            default: 'filterFromMeetingStartDate',
        },
        filterToMeetingStartDate_cache: {
            type: String,
            required: false,
            default: 'filterToMeetingStartDate',
        },
        filterFromMeetingEndDate_cache: {
            type: String,
            required: false,
            default: 'filterFromMeetingEndDate',
        },
        filterToMeetingEndDate_cache: {
            type: String,
            required: false,
            default: 'filterToMeetingEndDate',
        },
        filterMeetingStatus_cache: {
            type: String,
            required: false,
            default: 'filterMeetingStatus',
        },
    },
    data: function () {
        let vm = this;
        return {
            datatable_id: 'meetings-datatable-' + vm._uid,

            filterFromMeetingStartDate: sessionStorage.getItem(this.filterFromMeetingStartDate_cache) ? sessionStorage.getItem(this.filterFromMeetingStartDate_cache) : '',
            filterToMeetingStartDate: sessionStorage.getItem(this.filterToMeetingStartDate_cache) ? sessionStorage.getItem(this.filterToMeetingStartDate_cache) : '',

            filterFromMeetingEndDate: sessionStorage.getItem(this.filterFromMeetingEndDate_cache) ? sessionStorage.getItem(this.filterFromMeetingEndDate_cache) : '',
            filterToMeetingEndDate: sessionStorage.getItem(this.filterToMeetingEndDate_cache) ? sessionStorage.getItem(this.filterToMeetingEndDate_cache) : '',

            filterMeetingStatus: sessionStorage.getItem(this.filterMeetingStatus_cache) ? sessionStorage.getItem(this.filterMeetingStatus_cache) : 'all',

            processing_statuses: [
                { value: 'draft', name: 'Draft' },
                { value: 'discarded', name: 'Discarded' },
                { value: 'scheduled', name: 'Scheduled' },
                { value: 'completed', name: 'Completed' },
            ],

            profile: null,
            constants: constants,
        }
    },
    components: {
        datatable,
        CollapsibleFilters,
    },
    watch: {
        filterFromMeetingStartDate: function () {
            let vm = this;
            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterFromMeetingStartDate_cache, vm.filterFromMeetingStartDate);
        },
        filterToMeetingStartDate: function () {
            let vm = this;
            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterToMeetingStartDate_cache, vm.filterToMeetingStartDate);
        },
        filterFromMeetingEndDate: function () {
            let vm = this;
            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterFromMeetingEndDate_cache, vm.filterFromMeetingEndDate);
        },
        filterToMeetingEndDate: function () {
            let vm = this;
            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterToMeetingEndDate_cache, vm.filterToMeetingEndDate);
        },
        filterMeetingStatus: function () {
            let vm = this;
            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false); // This calls ajax() backend call.
            sessionStorage.setItem(vm.filterMeetingStatus_cache, vm.filterMeetingStatus);
        },
        filterApplied: function () {
            if (this.$refs.collapsible_filters) {
                this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
            }
        },
    },
    computed: {
        filterApplied: function () {
            if (this.filterFromMeetingStartDate === '' &&
                this.filterToMeetingStartDate === '' &&
                this.filterFromMeetingEndDate === '' &&
                this.filterToMeetingEndDate === '' &&
                this.filterMeetingStatus === 'all') {
                return false
            } else {
                return true
            }
        },
        datatable_headers: function () {
            return ['Number', 'Title', 'Location', 'Start Date', 'End date', 'Status', 'Action']

        },
        column_id: function () {
            return {
                data: "meeting_number",
                orderable: true,
                searchable: false,
                visible: true,
                name: "id",
            }
        },
        column_location: function () {
            return {
                data: "location",
                orderable: true,
                searchable: true,
                visible: true,
                name: "location",
            }
        },
        column_title: function () {
            return {
                data: "title",
                orderable: true,
                searchable: true,
                visible: true,
                name: "title",
            }
        },
        column_start_date: function () {
            return {
                data: "start_date",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function (data, type, full) {
                    if (full.start_date) {
                        return moment(full.start_date).format('DD/MM/YYYY') + moment(full.start_date).format(' h:mm:ss a')
                    }
                    return ''
                },
                name: "start_date",
            }
        },
        column_end_date: function () {
            return {
                data: "end_date",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function (data, type, full) {
                    if (full.end_date) {
                        return moment(full.end_date).format('DD/MM/YYYY') + moment(full.end_date).format(' h:mm:ss a')
                    }
                    return ''
                },
                name: "end_date",
            }
        },
        column_status: function () {
            return {
                data: "processing_status",
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
                    if (full.processing_status == 'Discarded') {
                        links += `<a href='#${full.id}' data-reinstate-meeting='${full.id}'>Reinstate</a><br/>`;
                    } else {
                        if (full.can_user_edit) {
                            if (full.processing_status == 'Scheduled') {
                                links += `<a href='/internal/meetings/${full.id}?action=edit'>Edit</a><br/>`;
                            } else {
                                links += `<a href='/internal/meetings/${full.id}'>Continue</a><br/>`;
                            }
                            if (full.processing_status == 'Draft') {
                                links += `<a href='#${full.id}' data-discard-meeting='${full.id}'>Discard</a><br/>`;
                            }
                        }
                        else {
                            links += `<a href='/internal/meetings/${full.id}?action=view'>View</a><br/>`;
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
            columns = [
                vm.column_id,
                vm.column_title,
                vm.column_location,
                vm.column_start_date,
                vm.column_end_date,
                vm.column_status,
                vm.column_action,
            ]
            search = true
            let buttons = [
                {
                    extend: 'excel',
                    title: 'Boranga Meeting Excel Export',
                    text: '<i class="fa-solid fa-download"></i> Excel',
                    className: 'btn btn-primary me-2 rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                },
                {
                    extend: 'csv',
                    title: 'Boranga Meeting CSV Export',
                    text: '<i class="fa-solid fa-download"></i> CSV',
                    className: 'btn btn-primary rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    }
                }
            ]
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
                    { responsivePriority: 1, targets: 0 },
                    { responsivePriority: 3, targets: -1, className: 'no-export' },
                    { responsivePriority: 2, targets: -2 }
                ],
                ajax: {
                    "url": this.url,
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function (d) {
                        d.filter_to_start_date = vm.filterToMeetingStartDate;
                        d.filter_from_start_date = vm.filterFromMeetingStartDate;
                        d.filter_to_end_date = vm.filterToMeetingEndDate;
                        d.filter_from_end_date = vm.filterFromMeetingEndDate;
                        d.filter_meeting_status = vm.filterMeetingStatus;
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
        },
    },
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
        },
        constructMeetingsTable: function () {
            this.$refs.meetings_datatable.vmDataTable.clear().draw();
        },
        createMeeting: async function () {
            let newMeetingId = null
            try {
                const createUrl = api_endpoints.meeting + "/";
                let payload = new Object();
                payload.meeting_type = 'meeting';
                let savedMeeting = await Vue.http.post(createUrl, payload);
                if (savedMeeting) {
                    newMeetingId = savedMeeting.body.id;
                }
                this.$router.push({
                    name: 'internal-meetings',
                    params: { meeting_id: newMeetingId },
                });
            }
            catch (err) {
                console.log(err);
                if (this.is_internal) {
                    return err;
                }
            }

        },
        discardMeeting: function (meeting_id) {
            let vm = this;
            swal.fire({
                title: "Discard Meeting",
                text: "Are you sure you want to discard this meeting?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Discard Meeting',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary'
                },
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    vm.$http.patch(api_endpoints.discard_meeting(meeting_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Discarded',
                                text: 'Your meeting has been discarded',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            });
        },
        reinstateMeeting: function (meeting_id) {
            let vm = this;
            swal.fire({
                title: "Reinstate Meeting",
                text: "Are you sure you want to reinstate this meeting?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Reinstate Meeting',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary'
                },
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    vm.$http.patch(api_endpoints.reinstate_meeting(meeting_id))
                        .then((response) => {
                            swal.fire({
                                title: 'Reinstated',
                                text: 'Your meeting has been reinstated',
                                icon: 'success',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            vm.$refs.meetings_datatable.vmDataTable.ajax.reload(helpers.enablePopovers, false);
                        }, (error) => {
                            console.log(error);
                        });
                }
            });
        },
        addEventListeners: function () {
            let vm = this;
            // External Discard listener
            vm.$refs.meetings_datatable.vmDataTable.on('click', 'a[data-discard-meeting]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-discard-meeting');
                vm.discardMeeting(id);
            });
            vm.$refs.meetings_datatable.vmDataTable.on('click', 'a[data-reinstate-meeting]', function (e) {
                e.preventDefault();
                var id = $(this).attr('data-reinstate-meeting');
                vm.reinstateMeeting(id);
            });
            vm.$refs.meetings_datatable.vmDataTable.on('childRow.dt', function (e, settings) {
                helpers.enablePopovers();
            });
        },
        fetchProfile: function () {
            let vm = this;
            Vue.http.get(api_endpoints.profile).then((response) => {
                vm.profile = response.body;
            })
        },
    },
    created: function () {
        let vm = this;
        vm.fetchProfile();
        this.$nextTick(() => {
            vm.addEventListeners();
        });
    },
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
