<template>
    <div class="">
        <div class="card card-default">
            <div class="card-header">
               History
            </div>
            <div class="card-body card-collapse">
                <table class="table small-table">
                        <tr>
                            <th>Last Modified</th>
                            <th></th>
                        </tr>
                        <tr v-for="r in reversion_ids">
                            <td>{{ r.created | formatDate }}</td>
                            <td><a id="history_id" :href="history_url+'version_id2='+ r.cur_version_id +'&version_id1='+ r.prev_version_id" target="_blank">Compare</a></td>
                        </tr>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'History',
    data: function() {
        let vm = this;
        return {

        }
    },
    props: {
        history_url: {
            type: String,
            default: '',
        },
        reversion_ids: {
            type: Array,
        },
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
}
</script>
