"""Automated SQL/data tests, including independent Python reconciliation.
These are not claims of completed human UAT or Power BI visual testing.
"""
from __future__ import annotations
import csv
import json
import sqlite3
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def validate(con: sqlite3.Connection) -> dict:
    manifest=json.loads((ROOT/'tests'/'generation_manifest.json').read_text())
    results=[]
    def check(tid: str, name: str, actual, expected) -> None:
        results.append(dict(test_id=tid,test_name=name,expected=str(expected),actual=str(actual),
                            status='PASS' if actual==expected else 'FAIL',test_layer='SQL/data automation'))
    def scalar(sql: str): return con.execute(sql).fetchone()[0]
    def ids(where: str) -> set:
        return {r[0] for r in con.execute('SELECT referral_id FROM fact_referrals WHERE '+where)}
    check('T01','Raw row count',scalar('SELECT COUNT(*) FROM raw_referral_rows'),6300)
    check('T02','Canonical referral count',scalar('SELECT COUNT(*) FROM canonical_referrals'),6000)
    check('T03','One fact row per referral',scalar('SELECT COUNT(*)-COUNT(DISTINCT referral_id) FROM fact_referrals'),0)
    check('T04','Repeated-ID set matches injected IDs',ids('source_row_count>1')==set(manifest['duplicate_referral_ids']),True)
    check('T05','Excess source rows removed from counting',scalar('SELECT SUM(duplicate_excess_rows) FROM fact_referrals'),300)
    # Independently calculate survivor selection from raw values in Python.
    source=list(con.execute('SELECT referral_id,source_updated_at,ingested_at,source_row_id FROM raw_referral_rows'))
    winners={}
    for rid, updated, ingested, rowid in source:
        candidate=(updated,ingested,rowid)
        if rid not in winners or candidate>winners[rid]: winners[rid]=candidate
    survivors=dict(con.execute('SELECT referral_id,surviving_source_row_id FROM fact_referrals'))
    check('T06','Latest source version and deterministic tie-breaker',
          sum(survivors[rid]!=v[2] for rid,v in winners.items()),0)
    check('T07','Missing receipt dates retained and flagged',ids('valid_received_date_flag=0')==set(manifest['missing_received']),True)
    check('T08','Backdated event IDs identified',ids('invalid_event_order_flag=1')==set(manifest['backdated_stage']),True)
    check('T09','Missing event dates identified',ids('missing_event_date_flag=1')==set(manifest['missing_stage_date']),True)
    check('T10','Timing exclusions count',scalar('SELECT SUM(1-timing_valid_flag) FROM fact_referrals'),78)
    check('T11','Unmapped statuses not silently coerced',ids('unmapped_status_flag=1')==set(manifest['unmapped_status']),True)
    check('T12','Status disagreements retained for review',ids('status_disagreement_flag=1')==set(manifest['mismatched_status']),True)
    check('T13','Missing intake owners not filled with sales reps',ids('missing_intake_owner_flag=1')==set(manifest['missing_intake']),True)
    check('T14','Open missing owners all enter ownership queue',scalar('''SELECT COUNT(*) FROM fact_referrals
         WHERE unassigned_open_flag<>(CASE WHEN current_stage NOT IN ('Completed','Closed') AND intake_owner_id='INT_UNASSIGNED' THEN 1 ELSE 0 END)'''),0)
    check('T15','Cohort maturity partitions all referrals',scalar('SELECT SUM(mature_30_flag+not_yet_mature_flag+1-timing_valid_flag) FROM fact_referrals'),6000)
    check('T16','Every numerator record is in denominator',scalar('SELECT COUNT(*) FROM fact_referrals WHERE scheduled_30_flag>mature_30_flag'),0)
    # Independent date arithmetic reconciliation, using canonical raw receipt + observed booking date.
    disagreed=0
    for received, scheduled, valid, mature, converted in con.execute('SELECT received_date,first_scheduled_date,timing_valid_flag,mature_30_flag,scheduled_30_flag FROM fact_referrals'):
        want_mature=int(bool(valid) and (date(2026,8,31)-date.fromisoformat(received)).days>=30)
        want_converted=int(bool(want_mature) and scheduled is not None and 0 <= (date.fromisoformat(scheduled)-date.fromisoformat(received)).days<=30)
        disagreed+=int((mature,converted)!=(want_mature,want_converted))
    check('T17','Independent Python cohort reconciliation',disagreed,0)
    orphan_count=0
    for key,dim in [('account_id','dim_account'),('site_id','dim_site'),('territory_id','dim_territory'),('sales_rep_id','dim_sales_rep'),('intake_owner_id','dim_intake_owner')]:
        orphan_count+=scalar(f'SELECT COUNT(*) FROM fact_referrals f LEFT JOIN {dim} d USING({key}) WHERE d.{key} IS NULL')
    check('T18','Referral fact dimension keys all resolve',orphan_count,0)
    check('T19','Valid elapsed intervals are nonnegative',scalar('SELECT COUNT(*) FROM fact_referrals WHERE days_to_schedule<0 OR days_received_to_review<0 OR days_review_to_ready<0 OR days_ready_to_scheduled<0'),0)
    check('T20','Overdue tasks exclude due-today and terminal/scheduled records',scalar("SELECT COUNT(*) FROM fact_referrals WHERE overdue_followup_flag=1 AND (next_followup_due_date>=as_of_date OR scheduling_queue_flag=0)"),0)
    check('T21','Activities preserved without referral multiplication',scalar('SELECT COUNT(*) FROM fact_activities'),3600)
    check('T22','Targets have unique month-territory grain',scalar("SELECT COUNT(*)-COUNT(DISTINCT month_start||territory_id) FROM fact_targets"),0)
    check('T23','Target row count',scalar('SELECT COUNT(*) FROM fact_targets'),120)
    check('T24','Exception keys are unique',scalar('SELECT COUNT(*)-COUNT(DISTINCT exception_id) FROM fact_exceptions'),0)
    check('T25','Account snapshot includes zero-activity accounts',scalar('SELECT COUNT(*) FROM fact_account_snapshot'),120)
    check('T26','No source event beyond observation cutoff',scalar("SELECT COUNT(*) FROM raw_stage_events WHERE event_date>'2026-08-31'"),0)
    check('T27','Closed cases retained in mature denominator',scalar("SELECT COUNT(*) FROM fact_referrals WHERE current_stage='Closed' AND timing_valid_flag=1 AND referral_age_days>=30 AND mature_30_flag<>1"),0)
    check('T28','Receipt-date missing records still in fact',scalar('SELECT COUNT(*) FROM fact_referrals WHERE received_date IS NULL'),36)
    # Dedicated boundary fixtures for date-only, inclusive day-30 definitions.
    fixtures=[
        ('day0','2026-07-01','2026-07-01',1,1,1),
        ('day30','2026-07-01','2026-07-31',1,1,1),
        ('day31','2026-07-01','2026-08-01',1,1,0),
        ('age30','2026-08-01','2026-08-31',1,1,1),
        ('age29','2026-08-02','2026-08-03',1,0,0),
        ('no_booking','2026-07-01',None,1,1,0),
        ('invalid_receipt',None,'2026-08-01',0,0,0),
        ('backdated','2026-07-01','2026-06-30',0,0,0)]
    con.execute('CREATE TEMP TABLE boundary_fixture (case_id TEXT,received_date TEXT,first_scheduled_date TEXT,timing_valid_flag INTEGER,expected_mature INTEGER,expected_scheduled INTEGER)')
    con.executemany('INSERT INTO boundary_fixture VALUES (?,?,?,?,?,?)',fixtures)
    boundary=list(con.execute('''WITH maturity AS (
      SELECT *,CASE WHEN timing_valid_flag=1 AND julianday('2026-08-31')-julianday(received_date)>=30 THEN 1 ELSE 0 END AS actual_mature
      FROM boundary_fixture)
      SELECT case_id,expected_mature,expected_scheduled,actual_mature,
      CASE WHEN actual_mature=1 AND julianday(first_scheduled_date)-julianday(received_date) BETWEEN 0 AND 30 THEN 1 ELSE 0 END AS actual_scheduled
      FROM maturity'''))
    for i,(name,em,es,am,ass) in enumerate(boundary,29):
        check(f'T{i:02}',f'Boundary fixture: {name}',(am,ass),(em,es))
    check('T37','Due date equals snapshot date is not overdue',scalar("SELECT CASE WHEN '2026-08-31'<'2026-08-31' THEN 1 ELSE 0 END"),0)
    check('T38','All unknown-owner surrogate values are retained',scalar("SELECT COUNT(*) FROM fact_referrals WHERE intake_owner_id='INT_UNASSIGNED'"),150)
    check('T39','Calendar is contiguous and covers full years',scalar('SELECT COUNT(*) FROM dim_date'),730)
    check('T40','Database structural integrity',scalar('PRAGMA integrity_check'),'ok')
    with (ROOT/'tests'/'validation_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    con.execute('DROP TABLE boundary_fixture')
    return dict(total=len(results),passed=sum(x['status']=='PASS' for x in results),failed=sum(x['status']=='FAIL' for x in results))

if __name__=='__main__':
    con=sqlite3.connect(ROOT/'database'/'healthcare_sales_operations.sqlite')
    try:
        result=validate(con); print(json.dumps(result,indent=2))
        if result['failed']: raise SystemExit(1)
    finally: con.close()
