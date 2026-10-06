-- Generated explicit raw-table schema. Empty CSV fields load as SQL NULL.

CREATE TABLE raw_territories (
  "territory_id" TEXT,
  "territory_name" TEXT,
  PRIMARY KEY (territory_id)
);

CREATE TABLE raw_sites (
  "site_id" TEXT,
  "site_name" TEXT,
  "territory_id" TEXT,
  PRIMARY KEY (site_id)
);

CREATE TABLE raw_sales_reps (
  "sales_rep_id" TEXT,
  "sales_rep_name" TEXT,
  "territory_id" TEXT,
  PRIMARY KEY (sales_rep_id)
);

CREATE TABLE raw_intake_owners (
  "intake_owner_id" TEXT,
  "intake_owner_name" TEXT,
  "site_id" TEXT,
  PRIMARY KEY (intake_owner_id)
);

CREATE TABLE raw_accounts (
  "account_id" TEXT,
  "account_name" TEXT,
  "territory_id" TEXT,
  "sales_rep_id" TEXT,
  "specialty" TEXT,
  "account_tier" TEXT,
  PRIMARY KEY (account_id)
);

CREATE TABLE raw_referral_rows (
  "source_row_id" TEXT,
  "referral_id" TEXT,
  "account_id" TEXT,
  "site_id" TEXT,
  "intake_owner_id" TEXT,
  "received_date" TEXT,
  "source_status" TEXT,
  "payer_group" TEXT,
  "service_line" TEXT,
  "source_updated_at" TEXT,
  "ingested_at" TEXT,
  PRIMARY KEY (source_row_id)
);

CREATE TABLE raw_stage_events (
  "event_id" TEXT,
  "referral_id" TEXT,
  "event_sequence" INTEGER,
  "stage_name" TEXT,
  "event_date" TEXT,
  PRIMARY KEY (event_id)
);

CREATE TABLE raw_followups (
  "followup_id" TEXT,
  "referral_id" TEXT,
  "created_date" TEXT,
  "due_date" TEXT,
  "completed_date" TEXT,
  "task_status" TEXT,
  PRIMARY KEY (followup_id)
);

CREATE TABLE raw_activities (
  "activity_id" TEXT,
  "account_id" TEXT,
  "sales_rep_id" TEXT,
  "activity_date" TEXT,
  "activity_type" TEXT,
  "outcome" TEXT,
  PRIMARY KEY (activity_id)
);

CREATE TABLE raw_targets (
  "month_start" TEXT,
  "territory_id" TEXT,
  "referral_target" INTEGER,
  PRIMARY KEY (month_start, territory_id)
);

CREATE TABLE raw_status_map (
  "status_key" TEXT,
  "standard_status" TEXT,
  PRIMARY KEY (status_key)
);

CREATE TABLE raw_project_config (
  "as_of_date" TEXT,
  "source_start_date" TEXT,
  "cohort_days" INTEGER,
  "followup_target_calendar_days" INTEGER,
  "stalled_stage_calendar_days" INTEGER,
  "random_seed" INTEGER,
  PRIMARY KEY (as_of_date)
);
