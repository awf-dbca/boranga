<template lang="html">
    <div id="threat_detail">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="threatForm">
                        <alert :show.sync="showError" type="danger"><strong>{{ errorString }}</strong></alert>
                        <alert v-if="change_warning && !isReadOnly" type="warning"><strong>{{ change_warning }}</strong>
                        </alert>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Category</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template v-if="!isReadOnly">
                                            <template
                                                v-if="threat_category_list && threat_category_list.length > 0 && threatObj.threat_category_id && !threat_category_list.map((d) => d.id).includes(threatObj.threat_category_id)">
                                                <input type="text" v-if="threatObj.threat_category"
                                                    class="form-control mb-3"
                                                    :value="threatObj.threat_category + ' (Now Archived)'" disabled />
                                                <div class="mb-3 text-muted">
                                                    Change threat category to:
                                                </div>
                                            </template>
                                            <select class="form-select"
                                                v-model="threatObj.threat_category_id">
                                                <option v-for="category in threat_category_list" :value="category.id"
                                                    v-bind:key="category.id">
                                                    {{ category.name }}
                                                </option>
                                            </select>
                                        </template>
                                        <template v-else>
                                            <input type="text" class="form-control" readonly
                                                v-model="threatObj.threat_category" />
                                        </template>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Threat Agent</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template v-if="!isReadOnly">
                                            <template
                                                v-if="threat_agent_list && threat_agent_list.length > 0 && threatObj.threat_agent_id && !threat_agent_list.map((d) => d.id).includes(threatObj.threat_agent_id)">
                                                <input type="text" v-if="threatObj.threat_agent"
                                                    class="form-control mb-3"
                                                    :value="threatObj.threat_agent + ' (Now Archived)'" disabled />
                                                <div class="mb-3 text-muted">
                                                    Change threat agent to:
                                                </div>
                                            </template>
                                            <select class="form-select"
                                                v-model="threatObj.threat_agent_id">
                                                <option v-for="agent in threat_agent_list" :value="agent.id"
                                                    v-bind:key="agent.id">
                                                    {{ agent.name }}
                                                </option>
                                            </select>
                                        </template>
                                        <template v-else>
                                            <input type="text" class="form-control" readonly
                                                v-model="threatObj.threat_agent" />
                                        </template>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Threat Comments</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea :disabled="isReadOnly" class="form-control"
                                            v-model="threatObj.comment">
        </textarea>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Current Impact?</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template v-if="current_impact_list && current_impact_list.length > 0">
                                            <div v-for="option in current_impact_list"
                                                class="form-check form-check-inline">
                                                <input :disabled="isReadOnly" type="radio" class="form-check-input"
                                                    :value="option.id" :id="'current_impact_' + option.id"
                                                    v-bind:key="option.id" v-model="threatObj.current_impact" />
                                                <label :for="'current_impact_' + option.id">{{ option.name }}</label>
                                            </div>
                                        </template>
                                        <template v-else>
                                            <div>There are no current impact options available</div>
                                        </template>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Potential Impact?</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template v-if="potential_impact_list && potential_impact_list.length > 0">
                                            <div v-for="option in potential_impact_list"
                                                class="form-check form-check-inline">
                                                <input :disabled="isReadOnly" type="radio" class="form-check-input"
                                                    :value="option.id" :id="'potential_impact_' + option.id"
                                                    v-bind:key="option.id" v-model="threatObj.potential_impact" />
                                                <label :for="'potential_impact_' + option.id">{{ option.name }}</label>
                                            </div>
                                        </template>
                                        <template v-else>
                                            <div>There are no potential impact options available</div>
                                        </template>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Potential Threat Onset?</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template
                                            v-if="potential_threat_onset_list && potential_threat_onset_list.length > 0">
                                            <div v-for="option in potential_threat_onset_list"
                                                class="form-check form-check-inline ">
                                                <input :disabled="isReadOnly" type="radio" class="form-check-input"
                                                    :value="option.id" :id="'potential_threat_onset_' + option.id"
                                                    v-bind:key="option.id" v-model="threatObj.potential_threat_onset" />
                                                <label :for="'potential_threat_onset_' + option.id">{{ option.name
                                                    }}</label>
                                            </div>
                                        </template>
                                        <template v-else>
                                            <div>There are no potential threat onset options available</div>
                                        </template>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left">Threat Source</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" readonly v-model="threatObj.source" />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label for="" class="control-label pull-left">Date observed: </label>
                                    </div>
                                    <div class="col-sm-9">
                                        <input :disabled="isReadOnly" type="date" class="form-control"
                                            name="date_observed" ref="date_observed"
                                            v-model="threatObj.date_observed" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div slot="footer">
                <button type="button" class="btn btn-secondary me-2" @click="cancel">Cancel</button>
                <template v-if="threat_action != 'view'">
                    <template v-if="threat_id">
                        <button type="button" v-if="updatingThreat" disabled class="btn btn-primary" @click="ok">
                            Updating <span class="spinner-border spinner-border-sm" role="status"
                                aria-hidden="true"></span>
                            <span class="visually-hidden">Loading...</span></button>
                        <button type="button" v-else class="btn btn-primary" @click="ok">Update</button>
                    </template>
                    <template v-else>
                        <button type="button" v-if="addingThreat" disabled class="btn btn-primary" @click="ok">Adding
                            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                            <span class="visually-hidden">Loading...</span></button>
                        <button type="button" v-else class="btn btn-primary" @click="ok">Add Threat</button>
                    </template>
                </template>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import { helpers } from "@/utils/hooks.js"
export default {
    name: 'Threat-Detail',
    components: {
        modal,
        alert
    },
    props: {
        url: {
            type: String,
            required: true
        },
        change_warning: {
            type: String,
            required: false
        },
    },
    data: function () {
        let vm = this;
        return {
            isModalOpen: false,
            form: null,
            threat_id: String,
            threat_action: String,
            threatObj: Object,
            threat_category_list: [],
            threat_agent_list: [],
            current_impact_list: [],
            potential_impact_list: [],
            potential_threat_onset_list: [],
            addingThreat: false,
            updatingThreat: false,
            validation_form: null,
            type: '1',
            errors: false,
            errorString: '',
            successString: '',
            success: false,
            validDate: false,
        }
    },
    computed: {
        showError: function () {
            var vm = this;
            return vm.errors;
        },
        title: function () {
            var action = this.threat_action;
            if (typeof action === "string" && action.length > 0) {
                var capitalizedAction = action.charAt(0).toUpperCase() + action.slice(1);
                return capitalizedAction + " Threat";
            } else {
                return "Invalid threat action"; // Or handle the error in an appropriate way
            }
        },
        isReadOnly: function () {
            return this.threat_action === "view" ? true : false;
        }
    },
    methods: {
        ok: function () {
            let vm = this;
            if ($(vm.form).valid()) {
                vm.sendData();
            }
        },
        cancel: function () {
            this.close()
        },
        close: function () {
            this.isModalOpen = false;
            this.threatObj = {};
            this.errors = false;
            $('.has-error').removeClass('has-error');
        },
        sendData: function () {
            let vm = this;
            vm.errors = false;
            vm.threatObj.date_observed = vm.threatObj.date_observed == "" ? null : vm.threatObj.date_observed
            let threatObj = JSON.parse(JSON.stringify(vm.threatObj));
            let formData = new FormData()

            if (vm.threatObj.id) {
                vm.updatingThreat = true;
                formData.append('data', JSON.stringify(threatObj));
                vm.$http.put(helpers.add_endpoint_json(vm.url, threatObj.id), formData, {
                    emulateJSON: true,
                }).then((response) => {
                    vm.updatingThreat = false;
                    vm.$parent.updatedThreats();
                    vm.close();
                }, (error) => {
                    vm.errors = true;
                    vm.errorString = helpers.apiVueResourceError(error);
                    vm.updatingThreat = false;
                });
            } else {
                vm.addingThreat = true;
                formData.append('data', JSON.stringify(threatObj));
                vm.$http.post(vm.url, formData, {
                    emulateJSON: true,
                }).then((response) => {
                    vm.addingThreat = false;
                    vm.close();
                    vm.$parent.updatedThreats();
                }, (error) => {
                    vm.errors = true;
                    vm.addingThreat = false;
                    vm.errorString = helpers.apiVueResourceError(error);
                });
            }
        },
        eventListeners: function () {
            let vm = this;
        }
    },
    created: async function () {
        let res = await this.$http.get('/api/threat/threat_list_of_values/');
        let threat_list_of_values_res = {};
        Object.assign(threat_list_of_values_res, res.body);
        this.threat_category_list = threat_list_of_values_res.active_threat_category_lists;
        this.threat_category_list.splice(0, 0,
            {
                id: null,
                name: null,
            });
        this.current_impact_list = threat_list_of_values_res.current_impact_lists;
        this.potential_impact_list = threat_list_of_values_res.potential_impact_lists;
        this.potential_threat_onset_list = threat_list_of_values_res.potential_threat_onset_lists;
        this.threat_agent_list = threat_list_of_values_res.threat_agent_lists;
        this.threat_agent_list.splice(0, 0,
            {
                id: null,
                name: null,
            });
    },
    mounted: function () {
        let vm = this;
        vm.form = document.forms.threatForm;
        this.$nextTick(() => {
            vm.eventListeners();
        });
    }
}
</script>
