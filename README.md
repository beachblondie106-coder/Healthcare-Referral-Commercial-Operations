# Healthcare Sales Operations: Referral Performance & Workflow Improvement

A synthetic healthcare operations portfolio project that turns referral, follow-up, activity, ownership, and target records into a reporting model for sales and intake operations.

Built with **Power BI Desktop, Power Query, DAX, SQL, SQLite, Python, and Excel/CSV** to demonstrate an end-to-end workflow from source-data preparation through operational reporting and follow-up prioritization.

> **Portfolio disclaimer:** This project uses synthetic data and a fictional outpatient-care organization. It was created independently for educational and portfolio purposes, does not contain protected health information, and does not represent any healthcare organization.

## Project Overview

Sales and intake teams need a shared view of referral progression, follow-up workload, partner-account activity, and performance against targets. This project brings those records into a validated reporting model that supports both leadership monitoring and day-to-day operational review.

The completed synthetic dataset contains:

- **6,000 unique referrals** from 6,300 raw source rows
- **5,480 follow-up tasks**
- **3,600 sales activities** across 120 partner accounts
- **6 territories**, 8 intake sites, 12 sales representatives, and 8 intake owners
- Referral activity from **January 2025 through August 2026**

## Business Questions Addressed

This project addresses three operational question areas:

- **Referral performance:** Are referral volumes meeting monthly and territory-level targets? What is the current pipeline mix by status, and how many referrals are completed?
- **Follow-up management:** How many follow-ups are open, completed, or overdue? Where is follow-up workload concentrated by territory, and how is it changing month to month?
- **Activity performance:** How much outreach is occurring, how broadly are accounts being engaged, what outcomes result from activities, and which territories have the highest activity volume?

Together, the report helps leadership identify performance gaps, monitor operational follow-through, and focus attention on territories or workflow stages needing intervention.

## Dashboard Preview

### 1. Referral Performance

![Referral Performance](docs/screenshots/referral-performance.png)

Tracks referral volume, completion status, monthly targets, pipeline status, and territory performance.

### 2. Follow-Up Management

![Follow-Up Management](docs/screenshots/follow-up-management.png)

Monitors created, completed, open, and overdue follow-ups, with workload views by month and territory.

### 3. Activity Performance

![Activity Performance](docs/screenshots/activity-performance.png)

Reviews outreach volume, account engagement, recorded activity outcomes, and territory coverage.

## Key Performance Indicators

| KPI | Portfolio Result |
|---|---:|
| Total referrals | 6,000 |
| Completed referrals | 4,292 |
| Referral target | 6,504 |
| Target attainment | 92.3% |
| Total follow-ups | 5,480 |
| Completed follow-ups | 4,910 |
| Open follow-ups | 570 |
| Overdue follow-ups | 458 |
| Total activities | 3,600 |
| Accounts engaged | 120 |

## Data and Reporting Design

- The source export contains **6,300 rows and 6,000 unique referrals**. The SQL keeps the raw records, applies a documented survivor rule, and reports one canonical referral per referral ID.
- **78 referrals** have unusable timing data and remain available for review instead of being silently excluded from the model.
- The 30-day scheduling cohort contains **5,602 mature referrals**, with **4,024 booked within 30 calendar days (71.8%)**.
- The model keeps sales-account ownership and intake-case ownership separate, and it records data-quality, ownership, status, and follow-up exceptions for review.
- **40 automated SQL/data checks passed** in the reproducible build.

## Analytical Workflow

1. Created synthetic referral, follow-up, activity, ownership, and target files with documented test conditions.
2. Loaded the source files into SQLite and profiled repeated IDs, missing values, and unmapped statuses.
3. Built canonical referral, dimension, fact, snapshot, and exception tables with SQL.
4. Exported reporting-ready tables for Power BI and created a calendar table, model relationships, and DAX measures.
5. Designed three Power BI Desktop pages for referral, follow-up, and activity performance.
6. Validated database structure, keys, date logic, data-quality flags, and KPI reconciliation with automated checks.

## Dashboard Features

- Referral volume and target-attainment monitoring
- Pipeline status and territory performance views
- Open and overdue follow-up workload analysis
- Monthly follow-up creation trend
- Outreach volume, account engagement, and activity-outcome analysis
- Data-quality and operational-exception tracking

## Tools and Skills Demonstrated

- **Power BI Desktop:** Data modeling, report design, KPI cards, charts, and filtering
- **Power Query and DAX:** Type handling, measures, calendar logic, and report-context calculations
- **SQL and SQLite:** Source profiling, transformations, reporting tables, and validation queries
- **Python:** Synthetic-data generation, database build automation, exports, and independent tests
- **Healthcare operations analytics:** Referral workflow, follow-up management, account ownership, and performance monitoring

## Repository Contents

| Location | Purpose |
|---|---|
| `docs/` | Project brief, KPI/data documentation, workflow playbook, and leadership materials |
| `docs/screenshots/` | Final Power BI report previews |
| `data/raw/` | Synthetic source exports, including intentional data-quality conditions |
| `data/processed/` | Reporting-ready Power BI import tables |
| `database/` | Ready-to-open SQLite database with raw and reporting layers |
| `sql/` | Schema, source profiling, reporting transformations, and analysis queries |
| `scripts/` | Synthetic-data generator, build runner, and validation logic |
| `powerbi/` | Model relationships, page specifications, and DAX reference |
| `tests/` | Validation evidence, SQL baseline, and manual testing checklist |

## How to View the Project

- Review the dashboard previews above for a quick view of the completed report.
- Open the SQLite database in DB Browser for SQLite to inspect the raw and reporting tables.
- The Power BI Desktop `.pbix` report remains local because it is too large for a standard Git repository.
- To rebuild the database and reporting exports from the included source files, install Python 3.10+ and run:

```powershell
python scripts/build_project.py
```

The build does not replace the raw source files. The optional `--regenerate` argument replaces only the project's synthetic source data and should not be used with real healthcare data.

## Project Notes

All organizations, accounts, referral records, and operational activity in this repository are synthetic. The report is a completed local Power BI Desktop case study; it has not been published to the Power BI Service and does not represent production deployment, formal user acceptance testing, clinical outcomes, or financial impact.
illips106) · [GitHub](https://github.com/beachblondie106-coder)

