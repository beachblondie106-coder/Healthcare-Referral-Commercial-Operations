# Power BI build guide | not yet built or visually tested

All inputs are synthetic. This package contains source data, a tested SQLite pipeline, reporting CSVs, and starter DAX. It does **not** contain a completed `.pbix` file. All three pages and the manual UAT remain to be built and verified in Power BI Desktop.

## 1. Import the reporting layer

Extract the ZIP before using any file. In Power BI Desktop, use **Get data > Text/CSV** and select each CSV in `data/processed` individually. Choose **Transform Data** before loading. Do not append or combine the folder: these files have different schemas. Use the base filename, without `.csv`, as each table name.

First import `fact_referrals`, `dim_account`, `dim_territory`, `dim_site`, `dim_sales_rep`, `dim_intake_owner`, and `dim_date`. Then import `fact_activities`, `fact_targets`, `fact_account_snapshot`, `fact_exceptions`, and `project_config`.

Set IDs and labels to **Text**, all date columns to **Date**, flags/counts/days/month_sort to **Whole number**, and `referral_change_pct` to **Decimal number**. Preserve empty dates as null. Use the full field dictionary in `docs/data_dictionary.csv`; do not trust CSV type detection without checking it. Treat ID fields as Do not summarize. The two `source_updated_at` fields exist only in raw data and are text timestamps in SQLite; the reporting CSVs use date-only analytics.

## 2. Add explicit relationships

Every relationship below is **one-to-many**, with **single-direction filtering from dimension to fact**. Remove unwanted auto-detected relationships. Do not connect fact tables directly, and do not connect dimensions to each other.

| One side | Many side | State |
|---|---|---|
| dim_date.date | fact_referrals.received_date | Active |
| dim_date.date | fact_referrals.first_completed_date | Inactive |
| dim_account.account_id | fact_referrals.account_id | Active |
| dim_territory.territory_id | fact_referrals.territory_id | Active |
| dim_site.site_id | fact_referrals.site_id | Active |
| dim_sales_rep.sales_rep_id | fact_referrals.sales_rep_id | Active |
| dim_intake_owner.intake_owner_id | fact_referrals.intake_owner_id | Active |
| dim_date.date | fact_activities.activity_date | Active |
| dim_account.account_id | fact_activities.account_id | Active |
| dim_territory.territory_id | fact_activities.territory_id | Active |
| dim_sales_rep.sales_rep_id | fact_activities.sales_rep_id | Active |
| dim_date.date | fact_targets.month_start | Active; month selections only |
| dim_territory.territory_id | fact_targets.territory_id | Active |
| dim_account.account_id | fact_account_snapshot.account_id | Active |
| dim_territory.territory_id | fact_account_snapshot.territory_id | Active |
| dim_sales_rep.sales_rep_id | fact_account_snapshot.sales_rep_id | Active |
| dim_account.account_id | fact_exceptions.account_id | Active |
| dim_territory.territory_id | fact_exceptions.territory_id | Active |
| dim_intake_owner.intake_owner_id | fact_exceptions.intake_owner_id | Active |

Leave `project_config` disconnected. Do **not** relate the date dimension to `fact_account_snapshot` or `fact_exceptions`: they describe the single August 31, 2026 snapshot. Account exceptions use the unassigned-intake sentinel only as a technical dimension member; `review_team` identifies the actual team responsible.

Mark `dim_date` as the date table using `date`. Sort `year_month` by `month_sort`. Use dimension columns, not fact-table copies of IDs, for slicers and chart categories. Keep account-territory and owner assignment static in this version; historical reassignment is not modeled.

## 3. Add the first five measures

Open `measures.dax` and add measures one at a time. Begin with `Unique Referrals`, `Dated Referrals`, `Mature 30-Day Referrals`, `Scheduled Within 30 Days`, and `Scheduled Within 30 Days %`. Set count formats to whole numbers and the percentage to `0.0%`.

With **no filters**, the SQL baseline is:

| Measure | Expected |
|---|---:|
| Unique Referrals | 6,000 |
| Dated Referrals | 5,964 |
| Mature 30-Day Referrals | 5,602 |
| Scheduled Within 30 Days | 4,024 |
| Scheduled Within 30 Days % | 71.8% |
| Timing Exclusions | 78 |
| Not Yet Mature | 320 |
| First Visits Completed, valid dated | 4,278 |
| Scheduling Queue Snapshot | 737 |
| Overdue Follow-up Snapshot | 408 |
| Unassigned Open Referrals Snapshot | 21 |

The no-filter reconciliation is 5,602 mature + 320 not mature + 78 timing-excluded = 6,000. A receipt-date slicer excludes the 36 referrals with missing receipt dates; keep a clearly labeled, unfiltered data-quality view for those records.

## 4. Build the three pages

### Page 1 — Growth & Referral Performance
Purpose: distinguish incoming activity, observed first-visit completions, and same-cohort progression.

Use KPI cards for dated referrals, first visits completed, 30-day scheduling rate, and median days to booking. Use `dim_date.year_month` for an activity trend with dated referrals and first visits completed. Add a separate cohort trend of scheduling rate with mature denominator counts in its tooltip. Add a territory/month actual-versus-target visual.

The date slicer uses **months**, not arbitrary days. Target comparisons permit only month/year and territory filters; the supplied target measure returns blank under account/site/rep/intake/payer/service/current-stage filters. Do not interpret a blank target as zero. Do not allocate targets to accounts without defining a new allocation assumption.

The completion measure switches the date relationship to **completion date**, while the scheduling rate stays on **receipt date**. Never divide monthly completed visits by monthly received referrals and label that conversion.

As of August 31, 2026, only August 1 receipts have 30 full elapsed days. Label August's cohort as partially observed and show the denominator. For complete-month cohort comparisons, use January 2025–July 2026. Do not apply that restriction to the activity trend, which may include August.

### Page 2 — Territory & Partner Accounts
Purpose: identify a specific partner-management action without treating small differences as proven performance problems.

Use `fact_account_snapshot` for fixed windows: August 2–31 vs. July 3–August 1, 2026. Display account name from `dim_account`, recent/prior counts, absolute and percentage change, current intake backlog, last outreach date, and suggested action. Show sales account owner separately from intake owner. No date slicer on this page; print both date windows on the page.

An account with fewer than five prior-window referrals does not meet the scenario's decline-action minimum. A zero prior count yields a blank percentage, not infinite growth. The suggested action is an ordered business rule, not a predictive model or a clinical priority. Review intake ownership and overdue tasks before requesting more referrals. Compare payer/service-line mix and workload before drawing conclusions about representatives.

Optional trend: use `dim_date.year_month` and `Dated Referrals`. Use the account dimension in selections so the trend and snapshot can respond to the same account; do not enable bidirectional fact relationships to force interactions.

### Page 3 — Workflow & Data Quality
Purpose: turn exceptions into owned actions.

Use snapshot cards for scheduling queue, overdue follow-up, missing follow-up tasks, and unassigned open referrals. Build a work table from `fact_referrals`: referral ID, account, current stage, intake owner, next due date, stage age, and review flags. Include records where scheduling_queue_flag = 1 **or** unassigned_open_flag = 1. Distinguish overdue tasks from tasks missing a due date; missing dates are not zero days overdue.

Add an exception chart/table from `fact_exceptions`, by issue and resolution status. Distinguish **issue records**, **affected referral records**, and **affected accounts**. DQ01 is resolved in reporting, not repaired in the source. There is no date slicer or hidden synchronized date filter on this page. Territory/account/intake filters are supported. A sales-rep filter is not provided for the exceptions fact.

## 5. Test before publishing

Run every manual case in `tests/manual_uat.csv` and record Actual result, Evidence, Tester, Date, and Status. The starting status is Not run, even though the SQL tests passed. Test completion-date switching, the August cohort boundary, the target-filter guard, no-date queue behavior, and multi-issue counts.

Add a footer: **Independent case study | Synthetic portfolio data | Snapshot: August 31, 2026**. The SQL baseline, not a mockup, is the reconciliation target. Export a PDF only after the actual report is built and checked.

Public sharing is optional and is not part of this starter package. Power BI Publish to web makes the report and underlying model data publicly accessible; review the full model before using it. No account or tenant permissions have been checked or changed.

## Technical references (accessed September 30, 2026)

- Microsoft, Text/CSV connector: https://learn.microsoft.com/en-us/power-query/connectors/text-csv
- Microsoft, star schema guidance: https://learn.microsoft.com/en-us/power-bi/guidance/star-schema
- Microsoft, USERELATIONSHIP: https://learn.microsoft.com/en-us/dax/userelationship-function-dax
- Microsoft, Publish to web warning: https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web
