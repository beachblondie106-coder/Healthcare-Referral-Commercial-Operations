# Source and reporting model

Every source and processed column is documented in `data_dictionary.csv`. Raw data is preserved exactly apart from CSV empty strings loading as SQL NULL. Reporting tables are prepared by readable SQL rather than by silently editing the input files.

| Table | Grain | Rows in this build |
|---|---|---:|
| raw_territories | One territory | 6 |
| raw_sites | One outpatient site | 8 |
| raw_sales_reps | One sales representative | 12 |
| raw_intake_owners | One intake owner | 8 |
| raw_accounts | One provider account | 120 |
| raw_referral_rows | One exported row/version, not one referral | 6,300 |
| raw_stage_events | One stage event within a referral | 26,511 |
| raw_followups | One follow-up task | 5,480 |
| raw_activities | One provider outreach activity | 3,600 |
| raw_targets | One month and territory | 120 |
| raw_status_map | One normalized alias | 17 |
| raw_project_config | One fixed scenario configuration | 1 |
| dim_date | One calendar date | 730 |
| dim_account | One provider account | 120 |
| dim_territory | One territory | 6 |
| dim_site | One site | 8 |
| dim_sales_rep | One sales owner including unassigned sentinel | 13 |
| dim_intake_owner | One intake owner including unassigned sentinel | 9 |
| fact_referrals | One canonical referral | 6,000 |
| fact_activities | One provider outreach activity | 3,600 |
| fact_targets | One month and territory | 120 |
| fact_account_snapshot | One account at frozen snapshot | 120 |
| fact_exceptions | One entity and exception rule at snapshot | 784 |
| project_config | One fixed scenario configuration | 1 |

`fact_referrals` is the central referral-grain table. Stage histories and follow-up tasks are aggregated before joining it, preventing one-to-many joins from multiplying referral counts. Provider outreach and monthly targets remain separate facts. The account snapshot is a fixed-window decision table, and exceptions have entity-plus-rule grain.

The Power BI model uses single-direction dimension-to-fact relationships. `dim_date` is active on referral receipt date and inactive on first completion date. Snapshot tables have no active date relationship. The 36 missing receipt dates remain in the referral fact and exception queue, but cannot be placed in a known receipt month.

The internal `canonical_referrals`, `stage_rollup`, and `followup_rollup` tables are SQL preparation layers, not extra Power BI imports. All available source events are before or on the fixed snapshot; the validator fails for a future event rather than silently accepting it. The stage model has no re-entry/rescheduling; the current stage is the last source sequence event.

## Limitations of version 0.1

Source PK/FK integrity failures, missing event history, changing account territories, duplicate stage IDs, and real-source schema drift are not deliberately modeled here. Foreign-key completeness is checked for this generated build. Adapting the pipeline to another source requires new profiling, validation and quarantine rules; the supplied inner joins must not be assumed safe for arbitrary real data. Static account/territory ownership is a scenario assumption.
