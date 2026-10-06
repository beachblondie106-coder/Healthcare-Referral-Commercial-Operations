# Referral exception review playbook — proposed workflow

**Status:** draft procedure for a fictional operational pilot; not deployed or clinically validated. It addresses data and administrative workflow, not medical triage. No real patients or employer systems are involved.

## Purpose and scope

Maintain a single counted referral, an accountable intake owner, a recognized stage, and a dated next action. The daily queue contains pending scheduling cases and any open cases without an intake owner. Sales representatives manage the provider relationship; intake owners manage referral progression.

## What the scenario suggests needs improvement

The raw export can repeat referral IDs, account ownership can be blank, intake ownership can be missing, and dates/statuses can be incomplete or inconsistent. These defects were deliberately generated. They are test cases, not evidence of employee behavior or a confirmed root-cause interview.

## Proposed daily operating procedure

1. **Validate the refresh — data steward.** Confirm source file counts, snapshot date, uniqueness, and key integrity. Run the automated tests. On a new structural/key failure, stop publication and preserve the last validated snapshot with a visible freshness warning. Expected synthetic exceptions do not make a structural test fail.
2. **Resolve counting — data steward.** Select the most recently updated source record per referral ID; use ingestion time and source row ID as deterministic tie-breakers. Preserve discarded versions in raw data. Treat similar account/date combinations with different referral IDs as separate referrals unless a real source owner supplies an authorized merge rule. A source row count is never the KPI.
3. **Assign ownership — intake supervisor or sales operations.** Open referrals with no intake owner go to the intake supervisor. Accounts with no sales owner go to sales operations. Do not assign either automatically from the other, and do not confuse the account-level sales task with referral-level intake work.
4. **Reconcile uncertain records — intake supervisor and data steward.** Inspect source receipt dates, event dates, and status conflicts. Do not infer a missing timestamp from a later stage or assume an unknown status is Closed. The report uses the event sequence provisionally; record the correction rationale before changing the source or mappings.
5. **Review administrative follow-up — intake owner.** Separate overdue open tasks, tasks missing a due date, and pending referrals with no open task. Record a next action and due date. The scenario assumes a first follow-up target of two calendar days and a stalled-stage review after more than seven days; these are portfolio assumptions, not healthcare deadlines. A due-today task is not overdue.
6. **Coordinate provider outreach — sales representative.** Resolve intake bottlenecks before pursuing more referrals from an affected account. Use last outreach date, recent/prior volumes, workload, payer mix, and the stated account-action rule. Never treat a contact count as proof of caused growth.
7. **Close with evidence — responsible owner and reviewer.** Capture the original value, corrected value, rationale, owner, change date, and reviewer. Rebuild the reporting tables and confirm that the issue clears without changing unrelated referral counts. Retain a before/after record and a regression-test result.

## Ownership and escalation

| Issue | Accountable role | Supporting role | Closure evidence |
|---|---|---|---|
| Repeated export ID / mapping rule | Data steward | Sales operations | Survivor rule, raw lineage, reconciled count |
| Missing or conflicting referral date/status | Intake supervisor | Data steward | Verified source correction and recalculated metric |
| Missing referral owner / follow-up task | Intake supervisor | Intake owner | Assigned owner and dated next action |
| Missing provider account sales owner | Sales operations | Sales manager | Account owner assignment |
| Partner outreach after operational review | Sales manager | Sales representative | Contact/action record, not an inferred causal outcome |

A proposed same-working-day review cadence and escalation at the next daily huddle are operating assumptions. Actual organizations would confirm staffing, authorized corrections, security, clinical escalation, and response standards with their own owners. No medical prioritization is implied by the dashboard's sorting order.

## Proposed evaluation, not achieved benefits

Use the supplied synthetic baseline to test report behavior. A real pilot would first establish its own baseline, then track source duplicate prevalence, open ownerless referrals, missing-task/due-date prevalence, overdue backlog, and the mature 30-day booking rate. Display volumes and denominators, separate completed data repairs from new incoming work, and avoid attributing changes to the pilot without a defensible comparison.

A decrease in counted referrals after deduplication is a reporting correction, not a decline in real referral demand. No hours saved, revenue increase, appointment uplift, or staffing reduction has been demonstrated. A workload what-if model is optional future scope and is not included in this starter version.
