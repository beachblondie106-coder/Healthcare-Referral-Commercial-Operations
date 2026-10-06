"""Load synthetic CSVs, execute visible SQL, export Power BI tables, and run tests.
No external packages or database server required. Rebuilds generated local outputs only.
"""
from __future__ import annotations
import argparse
import csv
import json
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from generate_data import generate

ROOT=Path(__file__).resolve().parents[1]
INTEGER_FIELDS={'event_sequence','referral_target','cohort_days','followup_target_calendar_days','stalled_stage_calendar_days','random_seed'}
PKS={'territories':['territory_id'],'sites':['site_id'],'sales_reps':['sales_rep_id'],
     'intake_owners':['intake_owner_id'],'accounts':['account_id'],'referral_rows':['source_row_id'],
     'stage_events':['event_id'],'followups':['followup_id'],'activities':['activity_id'],
     'targets':['month_start','territory_id'],'status_map':['status_key'],'project_config':['as_of_date']}
EXPORTS=['dim_date','dim_account','dim_territory','dim_site','dim_sales_rep','dim_intake_owner',
         'fact_referrals','fact_activities','fact_targets','fact_account_snapshot','fact_exceptions','project_config']

def export_query(conn: sqlite3.Connection, path: Path, query: str) -> None:
    cursor=conn.execute(query)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow([d[0] for d in cursor.description])
        writer.writerows(cursor)

def build() -> None:
    if sqlite3.sqlite_version_info < (3,25,0):
        raise RuntimeError('SQLite 3.25+ is required for ROW_NUMBER and LAG.')
    raw=ROOT/'data'/'raw'; processed=ROOT/'data'/'processed'; processed.mkdir(parents=True,exist_ok=True)
    if not (raw/'referral_rows.csv').exists():
        raise FileNotFoundError('Raw CSVs are missing. Run with --regenerate to create the synthetic sources.')
    db=ROOT/'database'/'healthcare_sales_operations.sqlite'; db.parent.mkdir(exist_ok=True)
    # Use a temporary database, preserving the prior working version if a build fails.
    tmp=db.with_suffix('.tmp.sqlite')
    if tmp.exists(): tmp.unlink()
    con=sqlite3.connect(tmp)
    try:
        schema=[]
        for name in PKS:
            with (raw/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f); fields=reader.fieldnames
                if fields is None: raise ValueError(f'Missing header: {name}')
                cols=',\n  '.join(f'"{c}" {"INTEGER" if c in INTEGER_FIELDS else "TEXT"}' for c in fields)
                stmt=f'CREATE TABLE raw_{name} (\n  {cols},\n  PRIMARY KEY ({", ".join(PKS[name])})\n);'
                schema.append(stmt); con.execute(stmt)
                placeholders=','.join('?' for _ in fields)
                con.executemany(f'INSERT INTO raw_{name} VALUES ({placeholders})',
                    [[None if r[c]=='' else int(r[c]) if c in INTEGER_FIELDS else r[c] for c in fields] for r in reader])
        (ROOT/'sql'/'00_schema.sql').write_text('-- Generated explicit raw-table schema. Empty CSV fields load as SQL NULL.\n\n'+'\n\n'.join(schema)+'\n',encoding='utf-8')
        con.executescript((ROOT/'sql'/'02_build_reporting.sql').read_text(encoding='utf-8'))
        con.execute('CREATE TABLE dim_date (date TEXT PRIMARY KEY, year INTEGER, month_number INTEGER, month_start TEXT, year_month TEXT, month_sort INTEGER)')
        start=date(2025,1,1); end=date(2026,12,31)
        days=[start+timedelta(days=i) for i in range((end-start).days+1)]
        con.executemany('INSERT INTO dim_date VALUES (?,?,?,?,?,?)',
            [(str(d),d.year,d.month,str(d.replace(day=1)),d.strftime('%Y-%m'),d.year*100+d.month) for d in days])
        con.commit()
        from validate_project import validate
        summary=validate(con)
        if summary['failed']:
            raise RuntimeError(f"Validation failed: {summary['failed']} tests. See tests/validation_results.csv")
        for table in EXPORTS:
            export_query(con,processed/f'{table}.csv',f'SELECT * FROM {table}')
        export_query(con,ROOT/'tests'/'sql_baseline.csv',
            '''SELECT COUNT(*) AS unique_referrals,SUM(valid_received_date_flag) AS dated_referrals,
               SUM(mature_30_flag) AS mature_30_day_cohort,SUM(scheduled_30_flag) AS scheduled_in_30,
               1.0*SUM(scheduled_30_flag)/NULLIF(SUM(mature_30_flag),0) AS scheduled_30_rate,
               SUM(not_yet_mature_flag) AS not_yet_mature,SUM(1-timing_valid_flag) AS timing_exclusions,
               SUM(open_referral_flag) AS open_referrals,SUM(scheduling_queue_flag) AS scheduling_queue,
               SUM(overdue_followup_flag) AS overdue_followup,SUM(unassigned_open_flag) AS open_without_intake_owner,
               SUM(stalled_stage_flag) AS stalled_stage_referrals,SUM(completed_observed_flag) AS observed_completed_first_visits,
               SUM(CASE WHEN timing_valid_flag=1 AND first_completed_date IS NOT NULL THEN 1 ELSE 0 END) AS valid_dated_completed_first_visits
               FROM fact_referrals''')
        row_counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in EXPORTS}
        run=dict(as_of_date='2026-08-31',sqlite_version=sqlite3.sqlite_version,python_version=sys.version.split()[0],
                 tests=summary,reporting_row_counts=row_counts,scope='Synthetic data and SQL validation only; Power BI not executed.')
        (ROOT/'tests'/'build_log.json').write_text(json.dumps(run,indent=2)+'\n',encoding='utf-8')
        con.close(); tmp.replace(db)
        print(json.dumps(run,indent=2))
    except Exception:
        con.close()
        if tmp.exists(): tmp.unlink()
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regenerate',action='store_true',help='Replace synthetic raw CSVs using the fixed seed before rebuilding.')
    args=parser.parse_args()
    if args.regenerate: generate()
    build()
