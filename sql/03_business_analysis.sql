-- Queries used to check reporting totals.

-- A. Core referral counts.
SELECT COUNT(*) AS unique_referrals,
       SUM(valid_received_date_flag) AS dated_referrals,
       SUM(mature_30_flag) AS mature_30_day_cohort,
       SUM(scheduled_30_flag) AS scheduled_in_30,
       ROUND(100.0*SUM(scheduled_30_flag)/NULLIF(SUM(mature_30_flag),0),2) AS scheduled_30_pct,
       SUM(not_yet_mature_flag) AS not_yet_mature,
       SUM(1-timing_valid_flag) AS timing_exclusions,
       SUM(open_referral_flag) AS open_referrals,
       SUM(scheduling_queue_flag) AS scheduling_queue,
       SUM(overdue_followup_flag) AS overdue_followup,
       SUM(unassigned_open_flag) AS open_without_intake_owner
FROM fact_referrals;

-- B. Referral cohort results by received month.
SELECT SUBSTR(received_date,1,7) AS received_month,
       COUNT(*) AS referrals_received,
       SUM(mature_30_flag) AS mature_cohort,
       SUM(scheduled_30_flag) AS scheduled_in_30,
       ROUND(100.0*SUM(scheduled_30_flag)/NULLIF(SUM(mature_30_flag),0),2) AS scheduled_30_pct,
       SUM(not_yet_mature_flag) AS not_yet_mature,
       SUM(1-timing_valid_flag) AS timing_exclusions
FROM fact_referrals WHERE valid_received_date_flag=1
GROUP BY SUBSTR(received_date,1,7) ORDER BY received_month;

-- C. Completed first visits by month.
SELECT SUBSTR(first_completed_date,1,7) AS completion_month,COUNT(*) AS completed_first_visits
FROM fact_referrals WHERE timing_valid_flag=1 AND first_completed_date IS NOT NULL
GROUP BY SUBSTR(first_completed_date,1,7) ORDER BY completion_month;

-- D. Territory and payer mix.
SELECT t.territory_name,r.payer_group,COUNT(*) AS referrals,
       SUM(mature_30_flag) AS mature_cohort,
       ROUND(100.0*SUM(scheduled_30_flag)/NULLIF(SUM(mature_30_flag),0),2) AS scheduled_30_pct,
       ROUND(AVG(CASE WHEN scheduled_observed_flag=1 THEN days_to_schedule END),1) AS mean_days_to_booking
FROM fact_referrals r JOIN dim_territory t USING(territory_id)
GROUP BY t.territory_name,r.payer_group ORDER BY t.territory_name,r.payer_group;

-- E. Current work queue.
SELECT referral_id,account_id,intake_owner_id,current_stage,referral_age_days,
       next_followup_due_date,days_in_current_stage,overdue_followup_flag,
       missing_followup_task_flag,unassigned_open_flag,manual_record_review_flag
FROM fact_referrals
WHERE scheduling_queue_flag=1 OR unassigned_open_flag=1
ORDER BY unassigned_open_flag DESC,manual_record_review_flag DESC,
         overdue_followup_flag DESC,days_in_current_stage DESC;

-- F. Exception counts.
SELECT rule_id,issue,resolution_status,COUNT(*) AS exception_count
FROM fact_exceptions GROUP BY rule_id,issue,resolution_status ORDER BY rule_id;

-- G. Monthly target attainment.
WITH actual AS (
  SELECT SUBSTR(received_date,1,7)||'-01' AS month_start,territory_id,COUNT(*) AS referrals
  FROM fact_referrals WHERE valid_received_date_flag=1 GROUP BY 1,2
)
SELECT t.month_start,t.territory_id,COALESCE(a.referrals,0) AS referrals,
       t.referral_target,ROUND(1.0*COALESCE(a.referrals,0)/t.referral_target,3) AS attainment
FROM fact_targets t LEFT JOIN actual a USING(month_start,territory_id)
ORDER BY t.month_start,t.territory_id;
