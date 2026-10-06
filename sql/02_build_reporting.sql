-- Build reporting tables from the loaded raw data.

CREATE TABLE canonical_referrals AS
WITH ranked AS (
    SELECT r.*,
           COUNT(*) OVER (PARTITION BY referral_id) AS source_row_count,
           ROW_NUMBER() OVER (
               PARTITION BY referral_id
               ORDER BY source_updated_at DESC, ingested_at DESC, source_row_id DESC
           ) AS survivor_rank
    FROM raw_referral_rows r
    WHERE source_updated_at <= (SELECT as_of_date || ' 23:59:59' FROM raw_project_config)
      AND ingested_at <= (SELECT as_of_date || ' 23:59:59' FROM raw_project_config)
)
SELECT * FROM ranked WHERE survivor_rank = 1;
CREATE UNIQUE INDEX ux_canonical_referral ON canonical_referrals(referral_id);

-- Roll stage events up to one row per referral.
CREATE TABLE stage_rollup AS
WITH sequenced AS (
    SELECT e.*,
           LAG(event_date) OVER (PARTITION BY referral_id ORDER BY event_sequence) AS previous_event_date,
           ROW_NUMBER() OVER (PARTITION BY referral_id ORDER BY event_sequence DESC) AS latest_rank
    FROM raw_stage_events e
), checked AS (
    SELECT s.*, c.received_date,
        CASE WHEN event_date IS NULL OR date(event_date) IS NULL THEN 1 ELSE 0 END AS missing_event_date,
        CASE WHEN julianday(event_date) < julianday(previous_event_date)
                   OR julianday(event_date) < julianday(c.received_date)
                   OR event_date > (SELECT as_of_date FROM raw_project_config)
             THEN 1 ELSE 0 END AS invalid_event_order
    FROM sequenced s JOIN canonical_referrals c USING (referral_id)
)
SELECT referral_id,
    MIN(CASE WHEN stage_name='In Review' THEN event_date END) AS first_review_date,
    MIN(CASE WHEN stage_name='Ready to Schedule' THEN event_date END) AS first_ready_date,
    MIN(CASE WHEN stage_name='Scheduled' THEN event_date END) AS first_scheduled_date,
    MIN(CASE WHEN stage_name='Completed' THEN event_date END) AS first_completed_date,
    MAX(CASE WHEN stage_name='Scheduled' THEN 1 ELSE 0 END) AS scheduled_observed_flag,
    MAX(CASE WHEN stage_name='Completed' THEN 1 ELSE 0 END) AS completed_observed_flag,
    MAX(CASE WHEN latest_rank=1 THEN stage_name END) AS current_stage,
    MAX(CASE WHEN latest_rank=1 THEN event_date END) AS current_stage_date,
    MAX(missing_event_date) AS missing_event_date_flag,
    MAX(invalid_event_order) AS invalid_event_order_flag
FROM checked GROUP BY referral_id;

CREATE TABLE followup_rollup AS
SELECT referral_id,
       MIN(CASE WHEN task_status='Completed' THEN completed_date END) AS first_followup_date,
       MAX(CASE WHEN task_status='Completed' THEN completed_date END) AS last_followup_date,
       MIN(CASE WHEN task_status='Open' THEN due_date END) AS next_followup_due_date,
       SUM(CASE WHEN task_status='Open' THEN 1 ELSE 0 END) AS open_task_count,
       SUM(CASE WHEN task_status='Open' AND due_date IS NULL THEN 1 ELSE 0 END) AS missing_due_date_count
FROM raw_followups GROUP BY referral_id;

CREATE TABLE dim_territory AS SELECT * FROM raw_territories;
CREATE TABLE dim_site AS SELECT * FROM raw_sites;
CREATE TABLE dim_sales_rep AS
SELECT * FROM raw_sales_reps
UNION ALL SELECT 'REP_UNASSIGNED','Unassigned sales account owner',NULL;
CREATE TABLE dim_intake_owner AS
SELECT * FROM raw_intake_owners
UNION ALL SELECT 'INT_UNASSIGNED','Unassigned intake owner',NULL;
CREATE TABLE dim_account AS
SELECT account_id, account_name, territory_id,
       COALESCE(sales_rep_id,'REP_UNASSIGNED') AS sales_rep_id,
       specialty, account_tier
FROM raw_accounts;
CREATE UNIQUE INDEX ux_dim_account ON dim_account(account_id);

CREATE TABLE fact_referrals AS
WITH joined AS (
    SELECT c.referral_id, c.source_row_id AS surviving_source_row_id,
        c.account_id, a.territory_id, c.site_id,
        COALESCE(a.sales_rep_id,'REP_UNASSIGNED') AS sales_rep_id,
        COALESCE(c.intake_owner_id,'INT_UNASSIGNED') AS intake_owner_id,
        c.received_date, c.payer_group, c.service_line,
        c.source_status, m.standard_status, c.source_row_count,
        c.source_row_count-1 AS duplicate_excess_rows,
        s.first_review_date, s.first_ready_date, s.first_scheduled_date, s.first_completed_date,
        s.scheduled_observed_flag, s.completed_observed_flag, s.current_stage, s.current_stage_date,
        s.missing_event_date_flag, s.invalid_event_order_flag,
        f.first_followup_date, f.last_followup_date, f.next_followup_due_date,
        COALESCE(f.open_task_count,0) AS open_task_count,
        COALESCE(f.missing_due_date_count,0) AS missing_due_date_count,
        cfg.as_of_date, cfg.cohort_days, cfg.followup_target_calendar_days, cfg.stalled_stage_calendar_days,
        CASE WHEN c.received_date IS NOT NULL AND date(c.received_date) IS NOT NULL
                       AND c.received_date BETWEEN cfg.source_start_date AND cfg.as_of_date
             THEN 1 ELSE 0 END AS valid_received_date_flag,
        CASE WHEN m.standard_status IS NULL THEN 1 ELSE 0 END AS unmapped_status_flag,
        CASE WHEN m.standard_status IS NOT NULL AND m.standard_status <> s.current_stage THEN 1 ELSE 0 END AS status_disagreement_flag,
        CASE WHEN a.sales_rep_id IS NULL THEN 1 ELSE 0 END AS missing_sales_owner_flag,
        CASE WHEN c.intake_owner_id IS NULL THEN 1 ELSE 0 END AS missing_intake_owner_flag
    FROM canonical_referrals c
    JOIN raw_accounts a USING (account_id)
    LEFT JOIN raw_status_map m ON LOWER(TRIM(c.source_status))=m.status_key
    JOIN stage_rollup s USING (referral_id)
    LEFT JOIN followup_rollup f USING (referral_id)
    CROSS JOIN raw_project_config cfg
), timed AS (
    SELECT *,
        CASE WHEN valid_received_date_flag=1 AND missing_event_date_flag=0 AND invalid_event_order_flag=0
             THEN 1 ELSE 0 END AS timing_valid_flag,
        CASE WHEN valid_received_date_flag=1 THEN CAST(julianday(as_of_date)-julianday(received_date) AS INTEGER) END AS referral_age_days,
        CASE WHEN current_stage NOT IN ('Completed','Closed') THEN 1 ELSE 0 END AS open_referral_flag,
        CASE WHEN current_stage IN ('Received','In Review','Ready to Schedule') THEN 1 ELSE 0 END AS scheduling_queue_flag
    FROM joined
), flags AS (
    SELECT *,
        CASE WHEN timing_valid_flag=1 THEN CAST(julianday(first_review_date)-julianday(received_date) AS INTEGER) END AS days_received_to_review,
        CASE WHEN timing_valid_flag=1 THEN CAST(julianday(first_ready_date)-julianday(first_review_date) AS INTEGER) END AS days_review_to_ready,
        CASE WHEN timing_valid_flag=1 THEN CAST(julianday(first_scheduled_date)-julianday(first_ready_date) AS INTEGER) END AS days_ready_to_scheduled,
        CASE WHEN timing_valid_flag=1 THEN CAST(julianday(first_scheduled_date)-julianday(received_date) AS INTEGER) END AS days_to_schedule,
        CASE WHEN timing_valid_flag=1 THEN CAST(julianday(as_of_date)-julianday(current_stage_date) AS INTEGER) END AS days_in_current_stage,
        CASE WHEN timing_valid_flag=1 AND referral_age_days>=cohort_days THEN 1 ELSE 0 END AS mature_30_flag,
        CASE WHEN timing_valid_flag=1 AND referral_age_days<cohort_days THEN 1 ELSE 0 END AS not_yet_mature_flag,
        CASE WHEN scheduling_queue_flag=1 AND next_followup_due_date<as_of_date THEN 1 ELSE 0 END AS overdue_followup_flag,
        CASE WHEN scheduling_queue_flag=1 AND open_task_count=0 AND referral_age_days>=followup_target_calendar_days
             THEN 1 ELSE 0 END AS missing_followup_task_flag
    FROM timed
)
SELECT *,
    CASE WHEN mature_30_flag=1 AND days_to_schedule BETWEEN 0 AND cohort_days THEN 1 ELSE 0 END AS scheduled_30_flag,
    CASE WHEN scheduling_queue_flag=1 AND days_in_current_stage>stalled_stage_calendar_days THEN 1 ELSE 0 END AS stalled_stage_flag,
    CASE WHEN open_referral_flag=1 AND missing_intake_owner_flag=1 THEN 1 ELSE 0 END AS unassigned_open_flag,
    CASE WHEN timing_valid_flag=0 OR unmapped_status_flag=1 OR status_disagreement_flag=1 THEN 1 ELSE 0 END AS manual_record_review_flag
FROM flags;
CREATE UNIQUE INDEX ux_fact_referral ON fact_referrals(referral_id);

CREATE TABLE fact_activities AS
SELECT x.activity_id,x.account_id,a.territory_id,
       COALESCE(x.sales_rep_id,'REP_UNASSIGNED') AS sales_rep_id,
       x.activity_date,x.activity_type,x.outcome
FROM raw_activities x JOIN raw_accounts a USING(account_id);
CREATE TABLE fact_targets AS SELECT * FROM raw_targets;

-- Current account summary as of the project snapshot date.
CREATE TABLE fact_account_snapshot AS
WITH ref AS (
    SELECT account_id,
        SUM(CASE WHEN received_date BETWEEN date(as_of_date,'-29 days') AND as_of_date THEN 1 ELSE 0 END) AS referrals_recent_30,
        SUM(CASE WHEN received_date BETWEEN date(as_of_date,'-59 days') AND date(as_of_date,'-30 days') THEN 1 ELSE 0 END) AS referrals_prior_30,
        SUM(scheduling_queue_flag) AS current_scheduling_queue,
        SUM(overdue_followup_flag) AS overdue_referrals,
        SUM(unassigned_open_flag) AS unassigned_open_referrals,
        SUM(mature_30_flag) AS mature_cohort_referrals,
        SUM(scheduled_30_flag) AS scheduled_in_30
    FROM fact_referrals GROUP BY account_id
), act AS (
    SELECT account_id, MAX(activity_date) AS last_outreach_date FROM fact_activities GROUP BY account_id
)
SELECT a.account_id,a.territory_id,a.sales_rep_id,cfg.as_of_date,
       COALESCE(r.referrals_recent_30,0) AS referrals_recent_30,
       COALESCE(r.referrals_prior_30,0) AS referrals_prior_30,
       COALESCE(r.referrals_recent_30,0)-COALESCE(r.referrals_prior_30,0) AS referral_change_count,
       CASE WHEN r.referrals_prior_30>0 THEN 1.0*(r.referrals_recent_30-r.referrals_prior_30)/r.referrals_prior_30 END AS referral_change_pct,
       COALESCE(r.current_scheduling_queue,0) AS current_scheduling_queue,
       COALESCE(r.overdue_referrals,0) AS overdue_referrals,
       COALESCE(r.unassigned_open_referrals,0) AS unassigned_open_referrals,
       COALESCE(r.mature_cohort_referrals,0) AS mature_cohort_referrals,
       COALESCE(r.scheduled_in_30,0) AS scheduled_in_30,
       x.last_outreach_date,
       CAST(julianday(cfg.as_of_date)-julianday(x.last_outreach_date) AS INTEGER) AS days_since_outreach,
       CASE WHEN a.sales_rep_id='REP_UNASSIGNED' THEN 'Assign account owner'
            WHEN COALESCE(r.unassigned_open_referrals,0)>0 THEN 'Resolve intake ownership'
            WHEN COALESCE(r.overdue_referrals,0)>0 THEN 'Coordinate intake follow-up'
            WHEN COALESCE(r.referrals_prior_30,0)>=5 AND COALESCE(r.referrals_recent_30,0)<=0.75*r.referrals_prior_30
                 AND (x.last_outreach_date IS NULL OR x.last_outreach_date<date(cfg.as_of_date,'-30 days')) THEN 'Review decline and reconnect'
            WHEN x.last_outreach_date IS NULL OR x.last_outreach_date<date(cfg.as_of_date,'-30 days') THEN 'Routine partner outreach'
            ELSE 'Maintain cadence' END AS suggested_action
FROM dim_account a CROSS JOIN raw_project_config cfg
LEFT JOIN ref r USING(account_id) LEFT JOIN act x USING(account_id);

-- Data-quality and ownership exceptions.
CREATE TABLE fact_exceptions AS
WITH issues AS (
    SELECT referral_id AS entity_id,'Referral' AS entity_type,account_id,territory_id,intake_owner_id,
           'DQ01' AS rule_id,'Repeated referral ID in source export' AS issue,
           'Resolved in reporting' AS resolution_status,'Data steward' AS review_team,
           'Retain raw versions; count one referral; confirm survivor rule.' AS required_action
    FROM fact_referrals WHERE source_row_count>1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ02','Missing or invalid receipt date','Awaiting review','Intake supervisor','Verify source receipt date; do not guess.' FROM fact_referrals WHERE valid_received_date_flag=0
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ03','Invalid event chronology','Awaiting review','Data steward','Compare source events; confirm sequence and correct date.' FROM fact_referrals WHERE invalid_event_order_flag=1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ04','Missing stage-event date','Awaiting review','Intake supervisor','Verify the missing event timestamp before timed reporting.' FROM fact_referrals WHERE missing_event_date_flag=1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ05','Unmapped source status','Awaiting review','Data steward','Confirm intended status; approve any mapping change.' FROM fact_referrals WHERE unmapped_status_flag=1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ06','Source status disagrees with event history','Awaiting review','Intake supervisor','Reconcile status; reporting uses event sequence provisionally.' FROM fact_referrals WHERE status_disagreement_flag=1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ07','Missing intake owner','Awaiting review','Intake supervisor','Assign accountable intake owner; do not substitute the sales rep.' FROM fact_referrals WHERE missing_intake_owner_flag=1
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ08','Open task missing due date','Awaiting review','Intake supervisor','Verify and enter a next follow-up due date.' FROM fact_referrals WHERE missing_due_date_count>0
    UNION ALL
    SELECT referral_id,'Referral',account_id,territory_id,intake_owner_id,'DQ09','Scheduling queue missing follow-up task','Awaiting review','Intake supervisor','Create a dated follow-up task after record review.' FROM fact_referrals WHERE missing_followup_task_flag=1
    UNION ALL
    SELECT account_id,'Account',account_id,territory_id,'INT_UNASSIGNED','DQ10','Missing sales account owner','Awaiting review','Sales operations','Assign sales account owner; retain intake ownership separately.' FROM dim_account WHERE sales_rep_id='REP_UNASSIGNED'
)
SELECT rule_id || ':' || entity_id AS exception_id,*,
       (SELECT as_of_date FROM raw_project_config) AS as_of_date
FROM issues;
CREATE UNIQUE INDEX ux_exception ON fact_exceptions(exception_id);

CREATE TABLE project_config AS SELECT * FROM raw_project_config;
