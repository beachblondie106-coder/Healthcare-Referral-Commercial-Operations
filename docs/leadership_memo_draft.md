# Leadership recommendation — starter draft

**To:** Fictional growth and intake leadership  
**From:** Lisa A. Phillips, independent portfolio project owner  
**Subject:** Establish referral-count and ownership controls before evaluating growth  
**Data:** Fully synthetic; January 1, 2025–August 31, 2026; snapshot August 31, 2026

## Decision requested

Approve the proposed exception-review workflow for a scenario pilot and assign a data steward, intake supervisor, and sales-operations owner. Complete report-level acceptance testing before using the dashboard to support decisions.

## Verified technical observations

The export contains 6,300 rows for 6,000 referral IDs. Counting rows would inflate referral volume by 300, or 5.0% relative to unique referrals. The SQL now counts one record per referral while preserving all original rows and documenting repeated IDs.

Seventy-eight referrals have unusable timing data and are retained in the exception process. Among 5,602 timing-valid referrals with a full 30-day observation window, 4,024 were booked within 30 days (71.8%). This is a synthetic baseline, not a performance benchmark. The current synthetic work queue contains 737 pre-booking referrals, including 408 with overdue follow-up tasks. There are 21 open referrals with no intake owner. These groups can overlap and must not be summed as a unique backlog total.

## Recommended first change

Create one accountable intake-owner field and a required next-action task for unresolved scheduling cases; reconcile unknown dates/statuses before treating their time metrics as valid. Sales operations should separately assign missing account owners. Preserve the deterministic referral-ID survivor rule and its audit trail.

## Success measures and ownership

The data steward owns counting and mapping controls; the intake supervisor owns assignment and task review; sales operations owns account ownership. Evaluate data-control pass rates, ownerless open referrals, missing next actions, overdue backlog, and the mature booking cohort, with each numerator and denominator defined. Do not equate a technical count correction with new appointments or financial savings.

## Readiness and limitations

Forty automated SQL/data tests passed in the supplied build. The Power BI model and starter DAX still require execution, visual reconciliation, and human UAT. No workflow has been implemented, no real business benefit has been measured, and no causal territory/sales conclusion is justified by generated data. Revise this memo after the actual report and acceptance evidence are complete.
