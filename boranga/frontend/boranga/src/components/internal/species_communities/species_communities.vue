<template lang="html">
    <div v-if="species_community" class="container" id="internalSpeciesCommunity">
      <div class="row" style="padding-bottom: 50px;">
        <h3>{{ display_group_type }} {{ display_number }} - {{display_name }}</h3>
        <h4>{{species_community.conservation_status.conservation_category }}</h4>
        <div v-if="!comparing" class="col-md-3">
            <!-- TODO -->
            <template>
                <div class="">
                    <div class="card card-default">
                        <div class="card-header">
                        Image
                        </div>
                        <div class="card-body card-collapse">
                            <div class="row">
                                <div class="col-sm-12">
                                    
                                    <div class="site-logo row" v-if="uploadedID">
                                        <img :src="uploadedID"  class="img-responsive"/>
                                        <span>
                                            <a @click="delete_image()" class="fa fa-trash-o" title="Remove file" style="cursor: pointer; color:red;"> delete image</a>
                                        </span>
                                    
                                    </div>
                                    <span class="btn btn-link btn-file pull-left" v-else-if="!uploadedID">Attach Image<input type="file" ref="uploadedID" @change="readFileID()"/></span>
                                    <span class="btn btn-link btn-file pull-left" v-else >&nbsp;Uploading...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            <template>
                <div class="card card-default">
                    <!-- <div class="card-body card-collapse"></div> -->
                </div>
                
            </template>

            <CommsLogs
                :comms_url="comms_url"
                :logs_url="logs_url"
                :comms_add_url="comms_add_url"
                :disable_add_entry="false"
            />

            <Submission v-if="canSeeSubmission"
                :submitter_first_name="submitter_first_name"
                :submitter_last_name="submitter_last_name"
                :lodgement_date="species_community.lodgement_date"
                class="mt-2"
            />

            <History v-if="canSeeSubmission"
                :history_url="history_url"
                :reversion_ids="species_community.reversion_ids"
                class="mt-2"
            />

            <div class="top-buffer-s">
                <div class="card card-default">
                    <div class="card-header">
                        Workflow 
                    </div>
                     <div class="card-body card-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ species_community.processing_status }}
                            </div>
                            <div class="col-sm-12">
                                <div class="separator"></div>
                            </div>
                            <!-- <div class="col-sm-12 top-buffer-s" v-if="!isFinalised && canAction"> -->
                            <div v-if='!isCommunity' class="col-sm-12 top-buffer-s">
                                <template v-if="hasUserEditMode">
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <button style="width:80%;" class="btn btn-primary top-buffer-s" @click.prevent="splitSpecies()">Split</button><br/>
                                        </div>
                                        <div class="col-sm-12">
                                            <button style="width:80%;" class="btn btn-primary top-buffer-s" @click.prevent="combineSpecies()">Combine</button><br/>
                                        </div>
                                        <div class="col-sm-12">
                                            <button style="width:80%;" class="btn btn-primary top-buffer-s" @click.prevent="renameSpecies()">Rename</button><br/>
                                        </div>
                                    </div>
                                </template>
                                <template v-if="canDiscard">
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <button style="width:80%;" class="btn btn-primary top-buffer-s" @click.prevent="discardSpeciesProposal()">Discard</button><br/>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>
                    
                </div>
            </div>
        </div>
        <div v-if="!comparing" class="col-md-1"></div>
        <!--<div class="col-md-8">-->
        <div :class="class_ncols">
            <div class="row">
                <template>
                    <div class="">
                        <div class="row">
                            <form :action="species_community_form_url" method="post" name="new_species" enctype="multipart/form-data">
                                <ProposalSpeciesCommunities 
                                    ref="species_communities" 
                                    :species_community="species_community" 
                                    id="speciesCommunityStart" 
                                    :is_internal="true">
                                </ProposalSpeciesCommunities>
                                <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
                                <input type='hidden' name="species_community_id" :value="1" />
                                <div class="row" style="margin-bottom: 50px">
                                    <div class="navbar fixed-bottom" style="background-color: #f5f5f5;">
                                        <div v-if="species_community.can_user_edit" class="container">
                                            <div class="col-md-12 text-end">
                                                <button v-if="savingSpeciesCommunity" class="btn btn-primary me-2 pull-right" style="margin-top:5px;" disabled >Save and Continue&nbsp;
                                                <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                                <button v-else class="btn btn-primary me-2 ull-right" style="margin-top:5px;" 
                                                @click.prevent="save()" :disabled="saveExitSpeciesCommunity || submitSpeciesCommunity">Save and Continue</button>
                                                
                                                <button v-if="saveExitSpeciesCommunity" class="btn btn-primary me-2 pull-right" style="margin-top:5px;" disabled >Save and Exit&nbsp;
                                                <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                                <button v-else class="btn btn-primary me-2 pull-right" style="margin-top:5px;" 
                                                @click.prevent="save_exit()" :disabled="savingSpeciesCommunity || submitSpeciesCommunity">Save and Exit</button>

                                                <button v-if="submitSpeciesCommunity" class="btn btn-primary pull-right" style="margin-top:5px;" disabled >Submit&nbsp;
                                                <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                                <button v-else class="btn btn-primary pull-right" style="margin-top:5px;" 
                                                @click.prevent="submit()" :disbaled="saveExitSpeciesCommunity || savingSpeciesCommunity">Submit</button>
                                            </div>
                                        </div>
                                        <div v-else-if="hasUserEditMode" class="container">
                                            <div class="col-md-12 text-end">
                                                <button v-if="savingSpeciesCommunity" class="btn btn-primary pull-right" style="margin-top:5px;" disabled >Save Changes&nbsp;
                                                <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                                <button v-else class="btn btn-primary pull-right" style="margin-top:5px;" @click.prevent="save()">Save Changes</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </template>
            </div>
        </div>
        </div>
        <SpeciesSplit ref="species_split" :species_community="species_community" :is_internal="true" @refreshFromResponse="refreshFromResponse"/>
        <SpeciesCombine ref="species_combine" :species_community="species_community" :is_internal="true" @refreshFromResponse="refreshFromResponse"/>
        <SpeciesRename ref="species_rename" :species_community_original="species_community" :is_internal="true" @refreshFromResponse="refreshFromResponse"/>
    </div>
</template>
<script>
import Vue from 'vue'
import datatable from '@vue-utils/datatable.vue'
import CommsLogs from '@common-utils/comms_logs.vue'
import Submission from '@common-utils/submission.vue'
import History from '@common-utils/history.vue'
import Workflow from '@common-utils/workflow.vue'

//import MoreReferrals from '@common-utils/more_referrals.vue'
import ProposalSpeciesCommunities from '@/components/form_species_communities.vue'
import SpeciesSplit from './species_split.vue'
import SpeciesCombine from './species_combine.vue'
import SpeciesRename from './species_rename.vue'
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
export default {
    name: 'InternalSpeciesCommunity',
    data: function() {
        let vm = this;
        return {
            "species_community":null,
            form: null,
            savingSpeciesCommunity:false,
            saveExitSpeciesCommunity: false,
            submitSpeciesCommunity: false,
            uploadedID: null,
            imageURL:'',

            
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            comparing: false,
        }
    },
    components: {
        datatable,
        CommsLogs,
        Submission,
        History,
        Workflow,
        ProposalSpeciesCommunities,
        SpeciesSplit,
        SpeciesCombine,
        SpeciesRename,
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
    watch: {
    },
    computed: {
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        isCommunity: function(){
            return this.species_community.group_type === "community"
        },
        species_community_form_url: function() {
          return (this.species_community.group_type === "community") ? 
                  `/api/community/${this.species_community.id}/community_save.json`: 
                  `/api/species/${this.species_community.id}/species_save.json`;
        },
        species_community_submit_url: function() {
          return (this.species_community.group_type === "community") ? 
                  `community`: 
                  `species`;
        },
        display_group_type: function() {
            let group_type_string=this.species_community.group_type
            // to Capitalize only first character
            return group_type_string.charAt(0).toUpperCase() + group_type_string.slice(1);
        },
        display_number: function() {
            return (this.species_community.group_type === "community") ? 
                    this.species_community.community_number : 
                    this.species_community.species_number;
        },
        display_name: function() {
            return (this.species_community.group_type === "community") ? 
                    (this.species_community.taxonomy_details != null) ? this.species_community.taxonomy_details.community_migrated_id : '' :
                    (this.species_community.taxonomy_details != null) ? this.species_community.taxonomy_details.scientific_name+" ("+this.species_community.taxonomy_details.taxon_name_id+")" : '';
        },
        class_ncols: function(){
            return this.comparing ? 'col-md-12' : 'col-md-8';
        },
        submitter_first_name: function(){
            if (this.species_community && this.species_community.submitter){
                return this.species_community.submitter.first_name
            } else {
                return ''
            }
        },
        submitter_last_name: function(){
            if (this.species_community && this.species_community.submitter){
                return this.species_community.submitter.last_name
            } else {
                return ''
            }
        },
        canSeeSubmission: function(){
            //return this.proposal && (this.proposal.processing_status != 'With Assessor (Requirements)' && this.proposal.processing_status != 'With Approver' && !this.isFinalised)
            //return this.proposal && (this.proposal.processing_status != 'With Assessor (Requirements)')
            return true
        },
        hasUserEditMode:function(){
            // Need to check for approved status as to show 'Save changes' button only when edit and not while view
            if(this.$route.query.action == 'edit'){
                return this.species_community && this.species_community.user_edit_mode ? true : false;
            }
            else{
                return false;
            }
        },
        canDiscard: function(){
            return this.species_community && this.species_community.processing_status === "Draft"? true:false;
        },
        comms_url: function() {
          return (this.species_community.group_type === "community") ? 
                  helpers.add_endpoint_json(api_endpoints.community,this.$route.params.species_community_id+'/comms_log'): 
                  helpers.add_endpoint_json(api_endpoints.species,this.$route.params.species_community_id+'/comms_log');
        },
        comms_add_url: function() {
          return (this.species_community.group_type === "community") ? 
                  helpers.add_endpoint_json(api_endpoints.community,this.$route.params.species_community_id+'/add_comms_log'): 
                  helpers.add_endpoint_json(api_endpoints.species,this.$route.params.species_community_id+'/add_comms_log');
        },
        logs_url: function() {
          return (this.species_community.group_type === "community") ? 
                  helpers.add_endpoint_json(api_endpoints.community,this.$route.params.species_community_id+'/action_log'): 
                  helpers.add_endpoint_json(api_endpoints.species,this.$route.params.species_community_id+'/action_log');
        },
        history_url: function(){
            return (this.species_community.group_type === "community") ? 
                  '/history/community/filtered/'+this.$route.params.species_community_id+'/?': 
                  '/history/species/filtered/'+this.$route.params.species_community_id+'/?';
        },
    },
    methods: {
        commaToNewline(s){
            return s.replace(/[,;]/g, '\n');
        },
        readFileID: async function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedID)[0];
            vm.imageURL= URL.createObjectURL(input.files[0])
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            //vm.imageURL= URL.createObjectURL()
            vm.uploadedID = _file;
            
            await vm.uploadImage();
        },
        uploadImage: async function() {
            let vm = this;
            vm.uploadingID = true;
            let data = new FormData();
            data.append('image2', vm.uploadedID);
            if (vm.uploadedID == null){
                vm.uploadingID = false;
                swal.fire({
                        title: 'Upload Image',
                        html: 'Please select an Image to upload.',
                        icon: 'error',
                        confirmButtonColor:'#226fbb'
                });
            } else {
                if(this.species_community.group_type=='community'){
                    var api_url= api_endpoints.community;
                }
                else{
                    var api_url= api_endpoints.species;
                }
                vm.$http.post(helpers.add_endpoint_json(api_url,(this.$route.params.species_community_id+'/upload_image')),data,{
                    emulateJSON:true
                }).then((response) => {
                    vm.uploadingID = false;
                    vm.uploadedID = null;
                    vm.uploadedID = response.body.image_doc;
                    vm.species_community.image_doc = response.body.image_doc;
                }, (error) => {
                    console.log(error);
                    vm.uploadingID = false;
                    vm.uploadedID = null;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        error_msg += key + ': ' + error.body[key] + '<br/>';
                    }
                    swal.fire({
                        title: 'Upload ID',
                        html: 'There was an error uploading your ID.<br/>' + error_msg,
                        icon: 'error',
                        confirmButtonColor:'#226fbb'
                    });
                });
            }
        },
        delete_image: async function() {
            let vm = this;
            if(this.species_community.group_type=='community'){
                    var api_url= api_endpoints.community;
                }
                else{
                    var api_url= api_endpoints.species;
                }
           
            if (vm.uploadedID == null){
                swal.fire({
                        title: 'Delete Image',
                        html: 'No Image uploaded.',
                        icon: 'error',
                        confirmButtonColor:'#226fbb'
                });
            } else {
                if(vm.species_community.image_doc)
                {
                    vm.$http.post(helpers.add_endpoint_json(api_url,(this.$route.params.species_community_id+'/delete_image')),{
                    emulateJSON:true
                }).then((response) => {
                    vm.uploadingID = false;
                    vm.uploadedID = null;
                    vm.uploadedID = response.body.image_doc;
                    vm.species_community.image_doc = response.body.image_doc;
                }, (error) => {
                    console.log(error);
                    vm.uploadingID = false;
                    vm.uploadedID = null;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        error_msg += key + ': ' + error.body[key] + '<br/>';
                    }
                    swal.fire({
                        title: 'Delete Image',
                        html: 'There was an error deleting your image.<br/>' + error_msg,
                        icon: 'error',
                        confirmButtonColor:'#226fbb'
                    });
                });
                }
                
            }
        },
        discardSpeciesProposal:function () {
            let vm = this;
            swal.fire({
                title: "Discard Application",
                text: "Are you sure you want to discard this proposal?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Discard Application',
                confirmButtonColor:'#d9534f'
            }).then((swalresult) => {
                if(swalresult.isConfirmed){
                    vm.$http.delete(api_endpoints.discard_species_proposal(vm.species_community.id))
                    .then((response) => {
                        swal.fire({
                            title: 'Discarded',
                            text: 'Your proposal has been discarded',
                            icon: 'success',
                            confirmButtonColor:'#226fbb',
                        });
                        vm.$router.push({
                        name: 'internal-species-communities-dash'
                        });
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {

            });
        },
        save: async function(e) {
            let vm = this;
            vm.savingSpeciesCommunity=true;
            let payload = new Object();
            Object.assign(payload, vm.species_community);
            vm.$http.post(vm.species_community_form_url,payload).then(res=>{
                swal.fire({
                    // 'Saved',
                    // 'Your changes has been saved',
                    // 'success'
                    title: "Saved",
                    text: "Your changes has been saved",
                    icon: "success",
                    confirmButtonColor:'#226fbb'
                });
              vm.savingSpeciesCommunity=false;
          },err=>{
            var errorText=helpers.apiVueResourceError(err); 
                swal.fire({
                    title: 'Save Error',
                    text: errorText,
                    icon: 'error',
                    confirmButtonColor:'#226fbb'
                });
            vm.savingSpeciesCommunity=false;
          });
        },
        save_exit: async function(e){
            let vm = this;
            vm.saveExitSpeciesCommunity=true;
            this.save(e);
            vm.saveExitSpeciesCommunity=false;
            // redirect back to dashboard
            vm.$router.push({
                    name: 'internal-species-communities-dash'
                });
        },
        save_before_submit: async function(e) {
            //console.log('save before submit');
            let vm = this;
            vm.saveError=false;

            let payload = new Object();
            Object.assign(payload, vm.species_community);
            const result = await vm.$http.post(vm.species_community_form_url,payload).then(res=>{
                //return true;
            },err=>{
                        var errorText=helpers.apiVueResourceError(err); 
                        swal.fire({
                            title: 'Submit Error',
                            //helpers.apiVueResourceError(err),
                            text: errorText,
                            icon: 'error',
                            confirmButtonColor:'#226fbb'
                        })
                        vm.submitSpeciesCommunity=false;
                        vm.saveError=true;
                //return false;
            });
            return result;
        },
        can_submit: function(){
            let vm=this;
            let blank_fields=[]
            if (vm.species_community.group_type == 'flora' || vm.species_community.group_type == 'fauna'){
                if (vm.species_community.taxonomy_id == null || vm.species_community.taxonomy_id == ''){
                    blank_fields.push(' Scientific Name is missing')
                }
            }
            else{
                if (vm.species_community.taxonomy_details.community_name == null || vm.species_community.taxonomy_details.community_name == ''){
                    blank_fields.push(' Community Name is missing')
                }
            }
            if(blank_fields.length==0){
                return true;
            }
            else{
                return blank_fields;
            }
        },
        submit: async function(){
            let vm = this;

            var missing_data= vm.can_submit();
            if(missing_data!=true){
                swal.fire({
                    title: "Please fix following errors before submitting",
                    text: missing_data,
                    icon:'error',
                    confirmButtonColor:'#226fbb'
                })
                //vm.paySubmitting=false;
                return false;
            }
            
            vm.submitSpeciesCommunity=true;
            swal.fire({
                title: "Submit",
                text: "Are you sure you want to submit this application?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: "submit",
                confirmButtonColor:'#226fbb'
            }).then(async (swalresult) => {
                if(swalresult.isConfirmed){
                    let result = await vm.save_before_submit()
                    if(!vm.saveError){
                        let payload = new Object();
                        Object.assign(payload, vm.species_community);
                        let submit_url = this.species_community.group_type === "community"? 
                                        helpers.add_endpoint_json(api_endpoints.community,vm.species_community.id+'/submit'): 
                                        helpers.add_endpoint_json(api_endpoints.species,vm.species_community.id+'/submit')
                        vm.$http.post(submit_url,payload).then(res=>{
                            vm.species_community = res.body;
                            // vm.$router.push({
                            //     name: 'submit_cs_proposal',
                            //     params: { conservation_status_obj: vm.conservation_status_obj}
                            // });
                        // TODO router should push to submit_cs_proposal for internal side 
                            vm.$router.push({
                                name: 'internal-species-communities-dash'
                            });
                        },err=>{
                            swal.fire({
                                title: 'Submit Error',
                                text: helpers.apiVueResourceError(err),
                                icon: 'error',
                                confirmButtonColor:'#226fbb'
                            });
                        });
                    }
                }
            },(error) => {
                vm.submitSpeciesCommunity=false;
            });
        },
        save_wo: function() {
            let vm = this;
            let formData = new FormData(vm.form);
            vm.$http.post(vm.proposal_form_url,formData).then(res=>{
                },err=>{
            });
        },
        refreshFromResponse:function(response){
            let vm = this;
            vm.original_species_community = helpers.copyObject(response.body);
            vm.species_community = helpers.copyObject(response.body);
        },
        splitSpecies: async function(){
            this.$refs.species_split.species_community_original = this.species_community;
            let newSpeciesId1 = null
            try {
                const createUrl = api_endpoints.species+"/";
                let payload = new Object();
                payload.group_type_id = this.species_community.group_type_id;
                let savedSpecies = await Vue.http.post(createUrl, payload);
                if (savedSpecies) {
                    newSpeciesId1 = savedSpecies.body.id;
                    Vue.http.get(`/api/species/${newSpeciesId1}/internal_species.json`).then(res => {
                        let species_obj=res.body.species_obj;
                        //--- to add empty documents array
                        species_obj.documents=[]
                        //---empty threats array added to store the select threat ids in from the child component
                        species_obj.threats=[]
                        this.$refs.species_split.new_species_list.push(species_obj); //--temp species_obj
                    },
                    err => {
                    console.log(err);
                    });
                }
            }
            catch (err) {
                console.log(err);
                if (this.is_internal) {
                    return err;
                }
            }
            let newSpeciesId2 = null
            try {
                const createUrl = api_endpoints.species+"/";
                let payload = new Object();
                payload.group_type_id = this.species_community.group_type_id
                let savedSpecies = await Vue.http.post(createUrl, payload);
                if (savedSpecies) {
                    newSpeciesId2 = savedSpecies.body.id;
                    Vue.http.get(`/api/species/${newSpeciesId2}/internal_species.json`).then(res => {
                        let species_obj=res.body.species_obj;
                        // to add documents id array from original species
                        species_obj.documents=[]
                        //---empty threats array added to store the select threat ids in from the child component
                        species_obj.threats=[]
                        this.$refs.species_split.new_species_list.push(species_obj); //--temp species_obj
                    },
                    err => {
                    console.log(err);
                    });
                }
            }
            catch (err) {
                console.log(err);
                if (this.is_internal) {
                    return err;
                }
            }
            this.$refs.species_split.isModalOpen = true;
        },
        combineSpecies: async function(){
            this.$refs.species_combine.original_species_combine_list.push(this.species_community); //--push current original into the array
            let newSpeciesId = null
            try {
                const createUrl = api_endpoints.species+"/";
                let payload = new Object();
                payload.group_type_id = this.species_community.group_type_id;
                let savedSpecies = await Vue.http.post(createUrl, payload);
                if (savedSpecies) {
                    newSpeciesId = savedSpecies.body.id;
                    Vue.http.get(`/api/species/${newSpeciesId}/internal_species.json`).then(res => {
                        let species_obj=res.body.species_obj;
                        //--- to add empty documents array
                        species_obj.documents=[]
                        //---empty threats array added to store the selected threat ids in from the child component
                        species_obj.threats=[]
                        this.$refs.species_combine.new_combine_species = species_obj; //---assign the new created species to the modal obj
                    },
                    err => {
                    console.log(err);
                    });
                }
                
            }
            catch (err) {
                console.log(err);
                if (this.is_internal) {
                    return err;
                }
            }
            this.$refs.species_combine.isModalOpen = true;
        },
        renameSpecies: async function(){
            let rename_species_obj = null;
            let newRenameSpecies = await Vue.http.get(`/api/species/${this.species_community.id}/rename_deep_copy.json`)
                if(newRenameSpecies){
                    rename_species_obj=newRenameSpecies.body.species_obj;
                    this.$refs.species_rename.new_rename_species = rename_species_obj;
                    this.$refs.species_rename.isModalOpen= true;
                }
        }
    },
    mounted: function() {
        let vm = this;
    },
    updated: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.form = document.forms.new_species;
        });
    },
    beforeRouteEnter: function(to, from, next) {
        //-------------get species object if received species id
        if(to.query.group_type_name === 'flora' || to.query.group_type_name === "fauna"){
            Vue.http.get(`/api/species/${to.params.species_community_id}/internal_species.json`).then(res => {
              next(vm => {
                vm.species_community = res.body.species_obj; //--temp species_obj
                vm.uploadedID= vm.species_community.image_doc;
              });
            },
            err => {
              console.log(err);
            });
        }
        //------get community object if received community id
        else{
            Vue.http.get(`/api/community/${to.params.species_community_id}/internal_community.json`).then(res => {
              next(vm => {
                vm.species_community = res.body.community_obj; //--temp community_obj
                vm.uploadedID= vm.species_community.image_doc;
              });
            },
            err => {
              console.log(err);
            });
        }
    },
    /*beforeRouteUpdate: function(to, from, next) {
          Vue.http.get(`/api/proposal/${to.params.species_community_id}.json`).then(res => {
              next(vm => {
                vm.proposal = res.body;
                vm.original_proposal = helpers.copyObject(res.body);
                
              });
            },
            err => {
              console.log(err);
            });
    }*/
}
</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
.separator {
    border: 1px solid;
    margin-top: 15px;
    margin-bottom: 10px;
    width: 100%;
}
</style>
