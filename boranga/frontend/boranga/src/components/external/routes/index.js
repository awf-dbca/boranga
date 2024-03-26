import ExternalDashboard from '../dashboard.vue'
import ExternalConservationStatusDash from '../conservation_status/dashboard.vue'
import ConservationStatusProposal from '../conservation_status/conservation_status_proposal.vue'
import ConservationStatusProposalSubmit from '../conservation_status/conservation_status_proposal_submit.vue'
import ExternalOccurrenceReportDash from '../occurrence/dashboard.vue'
import OccurrenceReportProposal from '../occurrence/occurrence_report_proposal.vue'
import OCRProposalSubmit from '../occurrence/ocr_proposal_submit.vue'
import Proposal from '../proposal.vue'
//import CommercialOperatorLicence from '../commercial_operator_licence.vue'
import ProposalApply from '../proposal_apply.vue'
import ProposalSubmit from '../proposal_submit.vue'
import Organisation from '../organisations/manage.vue'
import Compliance from '../compliances/access.vue'
import ComplianceSubmit from '../compliances/submit.vue'
import Approval from '../approvals/approval.vue'
import PaymentOrder from '@/components/common/tclass/payment_order.vue'
import PaymentDash from '@/components/common/payments_dashboard.vue'
export default
{
    path: '/external',
    component:
    {
        render(c)
        {
            return c('router-view')
        }
    },
    children: [
        /*{
            path: '/',
            component: ExternalDashboard,
            name: 'external-proposals-dash'
        },*/
        {
            path: 'conservation-status',
            component: ExternalConservationStatusDash,
            name:"external-conservation_status-dash"
        },
        {
            path: 'occurrence-report',
            component: ExternalOccurrenceReportDash,
            name:"external-occurrence_report-dash"
        },
        {
            path: 'occurrence-report/:occurrence_report_id',
            component: OccurrenceReportProposal,
            name:"draft_ocr_proposal"

        },
        {
            path: 'occurrence-report/submit',
            component: OCRProposalSubmit,
            name:"submit_ocr_proposal"

        },
        {
            path: 'organisations/manage/:org_id',
            component: Organisation
        },
        {
            path: 'compliance/:compliance_id',
            component: Compliance
        },
        {
            path: 'compliance/submit',
            component: ComplianceSubmit,
            name:"submit_compliance"
        },
        {
            path: 'approval/:approval_id',
            component: Approval,
        },
        {
            path: 'payment',
            component: PaymentDash,
            props: { level: 'external' }
        },
        {
            path: 'payment_order',
            component: PaymentOrder,
            name:"payment_order"
        },
        {
            path: 'proposal',
            component:
            {
                render(c)
                {
                    return c('router-view')
                }
            },
            children: [
                {
                    path: '/',
                    component: ProposalApply,
                    name:"apply_proposal"
                },
                {
                    path: 'submit',
                    component: ProposalSubmit,
                    name:"submit_proposal"
                },
                {
                    path: ':proposal_id',
                    component: Proposal,
                    name:"draft_proposal"
                },
                //{
                //    path: ':proposal_id',
                //    component: CommercialOperatorLicence,
                //    name:"draft_commercial_operator_licence"
                //},
            ]
        },
        {
            path: 'conservation_status',
            component: {
                render(c)
                {
                    return c('router-view')
                },
            },
            children: [
                {
                    path: ':conservation_status_id',
                    component: ConservationStatusProposal,
                    name:"draft_cs_proposal"
                },
                {
                    path: 'submit',
                    component: ConservationStatusProposalSubmit,
                    name:"submit_cs_proposal"
                },
                /*{
                    path: 'submit',
                    component: CnservationStatusSubmit,
                    name:"submit_cs_proposal"
                },*/
            ]
        },
    ]
}
