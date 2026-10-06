# KPI dictionary and measurement contract

All definitions are scenario decisions. The as-of date is August 31, 2026, not the computer's current date. Rates are computed from record-level counts, not averages of territory rates. Show the denominator beside every cohort rate.

| ID | Measure | Calculation | Boundary / limitation | Baseline / interpretation |
|---|---|---|---|---|
| K01 | Unique referrals | COUNTROWS(fact_referrals) | One canonical referral ID; unfiltered audit total is 6,000. Date filters can hide undated records. | All canonical referrals |
| K02 | Dated referral receipts | Count valid_received_date_flag = 1 | Group by receipt date; exclude the 36 missing receipt dates, not the referral records themselves. | 5,964 eligible receipt dates |
| K03 | Completed first visits | Count nonblank first_completed_date where timing_valid_flag = 1 | Group by completion date through an inactive date relationship; only one first visit per referral. | 4,278 valid dated; 4,332 observed in stage history |
| K04 | 30-day mature cohort | SUM(mature_30_flag) | Valid receipt and stage chronology; receipt age >= 30 days at the frozen snapshot. Closed and unscheduled referrals remain. | 5,602 mature; 320 not mature; 78 timing-excluded |
| K05 | Scheduled within 30 days % | SUM(scheduled_30_flag) / SUM(mature_30_flag) | Numerator is from the identical mature cohort; first booking occurs from day 0 through day 30 inclusive. Zero denominator returns blank. | 4,024 / 5,602 = 71.8% |
| K06 | Median days to booking | Median nonblank days_to_schedule | Only timing-valid referrals with an observed booking. Does not describe unresolved cases; compare with their current stage age. | Conditional on observed booking |
| K07 | Current scheduling queue | SUM(scheduling_queue_flag) | Current stage is Received, In Review, or Ready to Schedule. Scheduled cases are excluded from this pre-booking queue. | 737 at snapshot |
| K08 | Open referrals | SUM(open_referral_flag) | Anything except Completed/Closed; includes Scheduled. Separate from the pre-booking queue. | 857 at snapshot |
| K09 | Overdue follow-up | SUM(overdue_followup_flag) | Pre-booking queue with an open task due before the snapshot date. Due today is not overdue; missing dates are separate. | 408 referrals, not task rows |
| K10 | Stalled stage | SUM(stalled_stage_flag) | Pre-booking queue with valid timing and more than seven calendar days in its current stage. Not a regulatory deadline. | 583 referrals; invalid timing excluded |
| K11 | Open without intake owner | SUM(unassigned_open_flag) | Open stage and INT_UNASSIGNED. Do not substitute a sales account owner. | 21 at snapshot |
| K12 | Referral target attainment | Dated receipts / month-territory target | Compare like periods and territory only. Suppress under account/site/rep/intake/payer/service/status/day filtering. | Scenario targets, not external benchmarks |
| K13 | Account referral change | (recent 30 - prior 30) / prior 30 | Fixed windows Aug 2–31 vs. Jul 3–Aug 1, 2026. Prior zero gives blank, with counts visible. | Decline action requires prior >= 5 and decline >= 25% |
| K14 | Exception issues / affected records | Issue rows / distinct entity_id | A referral can have multiple rule violations. Separate referral and account entity types. DQ01 is resolved in reporting only. | 784 issue records; not 784 referrals |
| K15 | Timing exclusions | Count timing_valid_flag = 0 | 36 missing receipts + 24 backdated-stage records + 18 missing-stage-date records; injected sets do not overlap. | 78 records retained for review |
| K16 | Missing follow-up task | SUM(missing_followup_task_flag) | Pre-booking case age >= 2 calendar days and no open task. A completed historical contact does not replace a next task. | Scenario workflow rule |

## Important boundaries

A referral received August 1 has 30 elapsed days on August 31 and can enter the mature cohort. A referral received August 2 has only 29 elapsed days, even if already scheduled; neither its success nor its failure enters that cohort yet. A July 1 referral booked July 31 qualifies; one booked August 1 does not.

Current Closed status does not automatically remove a referral from the cohort or erase a valid prior booking. The measure evaluates a historical booking event, not whether the referral remains booked at the snapshot. There is no rescheduling logic in this version.

The 78 timing exclusions include invalid stage data even when a receipt date exists. Of these, 42 have receipt dates and still contribute to dated volume. The other 36 lack receipt dates and require an unfiltered exception view. Eighteen unknown source statuses and 24 status disagreements are additional review issues; their valid event timestamps still support timing metrics under the documented event-log authority assumption.

For complete-month cohort comparisons use receipts through July 2026. August volume and visit activity are complete for the synthetic snapshot, but the August receipt cohort is only partially mature. Period activity ratios are not conversion rates.

Stage-interval means or medians exclude unfinished transitions and therefore favor observed progress. Pair them with pending-stage age and backlog; do not call them the average waiting time of all referrals. Targets and follow-up thresholds were constructed for the scenario and are not clinical, legal, or industry standards.
