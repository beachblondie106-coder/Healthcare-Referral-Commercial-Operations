# Start here, Lisa

## What is ready

You have a complete **data, SQL, and Power BI Desktop case study**. The supplied files include synthetic source data, an executable SQLite database, cleaned reporting tables, test evidence, and a local Power BI report. Missing ownership and uncertain dates remain visible exceptions; they are not fabricated repairs.

The Power BI report has been visually reviewed locally but is not published to the Power BI Service. The `.pbix` file stays local and is intentionally excluded from Git because of its size. GitHub includes report previews in `docs/screenshots/`.

## Your first work session: understand the reporting issue

Open `docs/Project_Brief.pdf` and read the scope and measurement rules. Then open `database/healthcare_sales_operations.sqlite` in your SQLite client and run the first query in `sql/01_profile_sources.sql`:

```sql
SELECT
    COUNT(*) AS source_rows,
    COUNT(DISTINCT referral_id) AS unique_referrals,
    COUNT(*) - COUNT(DISTINCT referral_id) AS excess_rows
FROM raw_referral_rows;
```

Expected: **6,300 / 6,000 / 300**. This is the first business question: which number should leadership use, and why?

Next, read the first `ROW_NUMBER()` block in `sql/02_build_reporting.sql`. Explain in your own words why the newest source update is used first, why ingestion time and row ID break ties, and why different referral IDs must not be collapsed merely because they belong to the same account.

The ready-made database means you do not need to run Python to begin. Python is provided to reproduce the dataset and transformations, not as a second analytics platform you need to master for this case study.

## Power BI review note

Review `powerbi/BUILD_GUIDE.md` alongside the report previews in `docs/screenshots/`. The local report contains the completed Referral Performance, Follow-Up Management, and Activity Performance pages. Before using the case study in a formal setting, reconcile each reported measure to the SQL baseline and complete the manual UAT checklist.

## Completion checkpoints

1. Explain the source issue and reproduce the first SQL count.
2. Reconcile the Power BI model and measures to the supplied SQL baseline.
3. Complete the manual UAT checklist with evidence before treating the dashboard as validated.
4. Prepare a short walkthrough using the report previews and the leadership deck.

The local Power BI report is complete for portfolio review. Do not describe it as a production implementation or claim it improved real-world outcomes. Public sharing should follow your own review of the synthetic-data notice and portfolio materials.
