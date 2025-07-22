import 'vite/modulepreload-polyfill';

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import helpers from '@/utils/helpers';
import { extendMoment } from 'moment-range';
import VueSelect from 'vue-select';

import _ from 'lodash';
window._ = _;
import $ from 'jquery';
import select2 from 'select2';
window.$ = $;
import moment from 'moment';
window.moment = moment;
import swal from 'sweetalert2';
window.swal = swal;
select2();

import 'datatables.net-bs5';
import 'datatables.net-buttons-bs5';
import 'datatables.net-responsive-bs5';
import 'datatables.net-buttons/js/dataTables.buttons.js';
import JSZip from 'jszip';
window.JSZip = JSZip;
import 'datatables.net-buttons/js/buttons.html5.js';
import 'select2';
import 'jquery-validation';

import 'sweetalert2/dist/sweetalert2.css';
import 'select2/dist/css/select2.min.css';
import 'select2-bootstrap-5-theme/dist/select2-bootstrap-5-theme.min.css';
import '@/../node_modules/datatables.net-bs5/css/dataTables.bootstrap5.min.css';
import '@/../node_modules/datatables.net-responsive-bs5/css/responsive.bootstrap5.min.css';
import '@/../node_modules/@fortawesome/fontawesome-free/css/all.min.css';

extendMoment(moment);

// Add CSRF Token to every request
const customHeaders = new Headers({
    'X-CSRFToken': helpers.getCookie('csrftoken'),
});
const customHeadersJSON = new Headers({
    'X-CSRFToken': helpers.getCookie('csrftoken'),
    'Content-Type': 'application/json',
});

const app = createApp(App);

const fetch = window.fetch;
window.fetch = ((originalFetch) => {
    return async (...args) => {
        if (args.length > 1) {
            if (typeof args[1].body === 'string') {
                args[1].headers = customHeadersJSON;
            } else {
                args[1].headers = customHeaders;
            }
        }
        // Await the response to check status
        const response = await originalFetch.apply(this, args);

        // Handle 401/403 globally
        if (
            response.status === 401 &&
            // Only redirect to login for requests to boranga api endpoints
            args[0] &&
            typeof args[0] === 'string' &&
            new URL(args[0], window.location.origin).pathname.startsWith('/api')
        ) {
            window.location.href =
                '/login/?next=' + encodeURIComponent(window.location.pathname);
        } else if (response.status === 403) {
            swal.fire({
                icon: 'error',
                title: 'Access Denied',
                text: 'You do not have permission to perform this action.',
                customClass: {
                    confirmButton: 'btn btn-primary',
                },
            });
        }

        // Return the response so the caller can process it (e.g., await response.json())
        return response;
    };
})(fetch);

app.component('v-select', VueSelect).use(router);
router.isReady().then(() => app.mount('#app'));
