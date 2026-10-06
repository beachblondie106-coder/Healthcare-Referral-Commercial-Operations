# Requirements and scope — version 0.1

**Independent scenario, not stakeholder interviews.** Lisa A. Phillips is the project owner. The personas below are fictional report users. Requirements are proposed for this portfolio scenario and have not been approved by an employer.

## Decision and users

Leadership asks: Where are referrals getting delayed or failing to progress, which partner accounts need attention, and what should sales and intake operations change?

The growth leader reviews incoming volume and territory targets. The sales manager prioritizes partner conversations. The intake supervisor assigns and escalates work. The data steward maintains mappings and exception controls. They share measures, but they do not share the same ownership responsibility.

## Functional requirements

| ID | User | Required capability | SQL evidence | Human test |
|---|---|---|---|---|
| R01 | Growth leader | Use one referral per referral ID, while retaining raw source versions. | T01–T06 | U01 |
| R02 | Business analyst | Use the same mature receipt cohort in both the 30-day numerator and denominator. | T15–T17; T27; T29–T36 | U02 |
| R03 | Operations leader | Trend completed first visits by completion date, not receipt date. | SQL analysis C | U03 |
| R04 | Data steward | Standardize known aliases; route unknown/conflicting statuses to review. | T11–T12 | U04 |
| R05 | Intake supervisor | Identify every open referral missing an intake owner; keep sales ownership separate. | T13–T14; T38 | U05 |
| R06 | Intake team | Separate overdue, due-today, missing-due-date, and missing-task cases. | T20; T37 | U06 |
| R07 | Sales operations | Compare targets only at their defined month/territory grain. | T22–T23; SQL analysis G | U07 |
| R08 | Data steward | Retain invalid/undated referrals in the audit population and show metric exclusions. | T07–T10; T28 | U08 |
| R09 | Sales manager | Show fixed account comparison windows, small bases, and an explained next action. | T25; account snapshot | U09 |
| R10 | Report consumer | Distinguish issue counts, affected referral counts, and affected account counts. | T24; SQL analysis F | U10 |
| R11 | All consumers | Make the snapshot date visible and prevent date filters from hiding current backlog. | T26; snapshot flags | U11 |
| R12 | Project owner | Publish only synthetic data and label incomplete deliverables honestly. | Generation manifest; build log | U12 |

## Scenario boundaries

One fictional organization; one receipt-to-first-appointment process; three Power BI pages. Eight sites, six territories, 120 accounts, 12 sales representatives, and eight intake owners. Source receipts span January 1, 2025–August 31, 2026, with a frozen August 31 snapshot. Date-only precision means calendar-day intervals; no business-hours, holiday, or timezone calculations.

The stage sequence is Received → In Review → Ready to Schedule → Scheduled → Completed, with an alternative Closed exit. In Review is an administrative intake stage, not a clinical assessment. Booking is not attendance. Clinical urgency and medical necessity are not modeled. No repeated treatments, appointment rescheduling, finance/revenue estimates, real patient data, live CRM integration, or causal sales-performance claims.

Account and territory ownership are static throughout the scenario. This is a limitation, not an implemented historical assignment model. There is no geographic mapping of real locations.

## Nonfunctional acceptance

The raw data must remain intact; the build must reproduce outputs from a fixed seed; definitions must disclose exclusions and assumptions; DAX must reconcile to SQL under equivalent filters; and public-facing materials must say synthetic data. Keep SQL readable enough for the project owner to explain joins, row grain, survivor choice, and observation windows.

## Definition of done

The completed portfolio will contain a reviewed requirements/KPI document, reproducible SQL, a functioning three-page Power BI report, screenshots/PDF export of that actual report, automated and manual test evidence, an operational procedure, and a final one-page leadership memo. Version 0.1 satisfies the data-and-SQL foundation only. The starter DAX and manual UAT are not yet validated in Power BI, and no workflow pilot has occurred.
