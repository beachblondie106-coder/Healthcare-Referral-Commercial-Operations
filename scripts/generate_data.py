"""Generate deterministic synthetic portfolio data; never reads real records.
Python 3.10+ standard library only. Run from any directory.
"""
from __future__ import annotations
import calendar
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SEED = 9302026
START = date(2025, 1, 1)
AS_OF = date(2026, 8, 31)
N = 6000

def write_csv(name: str, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f'No rows to write for {name}')
    RAW.mkdir(parents=True, exist_ok=True)
    with (RAW / f'{name}.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def iso(d: date | None) -> str:
    return d.isoformat() if d else ''

def generate() -> None:
    rng = random.Random(SEED)
    territories = [dict(territory_id=f'T{i:02}', territory_name=name)
                   for i, name in enumerate(['North', 'South', 'East', 'West', 'Central', 'Coastal'], 1)]
    sites = [dict(site_id=f'S{i:02}', site_name=f'Synthetic Outpatient Site {i:02}',
                  territory_id=f'T{t:02}') for i, t in enumerate([1, 2, 3, 4, 5, 6, 3, 6], 1)]
    reps = [dict(sales_rep_id=f'REP{i:02}', sales_rep_name=f'Synthetic Sales Rep {i:02}',
                 territory_id=f'T{(i-1)//2+1:02}') for i in range(1, 13)]
    owners = [dict(intake_owner_id=f'INT{i:02}', intake_owner_name=f'Synthetic Intake Owner {i:02}',
                   site_id=f'S{i:02}') for i in range(1, 9)]
    accounts = []
    for i in range(1, 121):
        t = (i-1)//20 + 1
        accounts.append(dict(account_id=f'ACC{i:03}', account_name=f'Synthetic Provider Account {i:03}',
            territory_id=f'T{t:02}', sales_rep_id=f'REP{2*t-1+(i%2):02}',
            specialty=rng.choice(['Rheumatology', 'Neurology', 'Gastroenterology', 'Dermatology', 'Primary care']),
            account_tier=rng.choices(['A', 'B', 'C'], [25, 45, 30])[0]))
    for i in [7, 28, 46, 69, 84, 113]:
        accounts[i-1]['sales_rep_id'] = ''
    date_pool = [START + timedelta(days=i) for i in range((AS_OF-START).days+1)]
    weights = [1 + .025*((d.year-2025)*12+d.month-1) + (.12 if d.month in [3, 6, 9, 12] else 0) for d in date_pool]
    synonyms = {
        'Received': ['received', ' NEW ', 'Received'],
        'In Review': ['In Review', 'in_review', 'review'],
        'Ready to Schedule': ['ready to schedule', 'ready', 'Ready_to_Schedule'],
        'Scheduled': ['scheduled', ' SCHED ', 'booked'],
        'Completed': ['completed', 'complete', 'VISIT COMPLETE'],
        'Closed': ['closed', 'cancelled', 'CLOSED - NO VISIT']}
    referrals, events, followups = [], [], []
    actual_receipts, current_stages = {}, {}
    for i in range(1, N+1):
        rid = f'REF{i:06}'
        received = rng.choices(date_pool, weights=weights)[0]
        # Unequal account and territory mix is intentional, not real-world evidence.
        a = rng.choices(accounts, weights=[1.7 if x['account_tier']=='A' else 1.0 if x['account_tier']=='B' else .55 for x in accounts])[0]
        site = rng.choice([s for s in sites if s['territory_id']==a['territory_id']])
        payer = rng.choices(['Commercial', 'Medicare Advantage', 'Traditional Medicare', 'Medicaid', 'Other'], [38, 31, 16, 11, 4])[0]
        review = received + timedelta(days=rng.randint(1, 5))
        ready = review + timedelta(days=rng.randint(1, 9) + (8 if a['territory_id']=='T03' else 0) + (5 if payer=='Medicaid' else 0))
        scheduled = ready + timedelta(days=rng.randint(1, 15) + (15 if rng.random()<.12 else 0))
        completed = scheduled + timedelta(days=rng.randint(3, 21))
        path = [('Received', received), ('In Review', review), ('Ready to Schedule', ready), ('Scheduled', scheduled), ('Completed', completed)]
        u = rng.random()
        if u < .10:  # Deliberately persistent unresolved work, not a forecast.
            path = path[:rng.choice([1, 2, 3])]
        elif u < .24:
            last = rng.choice([1, 2, 3, 4])
            path = path[:last]
            path.append(('Closed', path[-1][1] + timedelta(days=rng.randint(2, 9))))
        visible = [(s, d) for s, d in path if d <= AS_OF]
        stage, last_date = visible[-1]
        for j, (st, dt) in enumerate(visible, 1):
            events.append(dict(event_id=f'EVT{len(events)+1:07}', referral_id=rid, event_sequence=j,
                               stage_name=st, event_date=iso(dt)))
        actual_receipts[rid] = received
        current_stages[rid] = stage
        referrals.append(dict(source_row_id=f'ROW{i:07}', referral_id=rid, account_id=a['account_id'],
            site_id=site['site_id'], intake_owner_id=f"INT{int(site['site_id'][1:]):02}",
            received_date=iso(received), source_status=rng.choice(synonyms[stage]),
            payer_group=payer, service_line=rng.choices(['Infusion', 'Injection', 'Other outpatient'], [60, 30, 10])[0],
            source_updated_at=iso(AS_OF)+' 12:00:00', ingested_at=iso(AS_OF)+' 18:00:00'))
        age = (AS_OF-received).days
        if age >= 1 and rng.random()<.82:
            done = received + timedelta(days=min(age, rng.randint(1, 6)))
            followups.append(dict(followup_id=f'FU{len(followups)+1:07}', referral_id=rid,
                created_date=iso(received), due_date=iso(received+timedelta(days=2)),
                completed_date=iso(done), task_status='Completed'))
        if stage in ['Received', 'In Review', 'Ready to Schedule'] and rng.random()<.78:
            created = max(received, AS_OF-timedelta(days=rng.randint(0, 15)))
            due = created + timedelta(days=2)
            followups.append(dict(followup_id=f'FU{len(followups)+1:07}', referral_id=rid,
                created_date=iso(created), due_date='' if rng.random()<.07 else iso(due),
                completed_date='', task_status='Open'))
    # Explicitly injected, disjoint date defects. Truth is for tests only, not a reporting input.
    all_ids = [r['referral_id'] for r in referrals]
    missing_received = set(rng.sample(all_ids, 36))
    chronology_candidates = sorted({e['referral_id'] for e in events if e['stage_name']=='In Review'}-missing_received)
    backdated = set(rng.sample(chronology_candidates, 24))
    schedule_candidates = sorted({e['referral_id'] for e in events if e['stage_name']=='Scheduled'}-missing_received-backdated)
    missing_event_date = set(rng.sample(schedule_candidates, 18))
    available = sorted(set(all_ids)-missing_received-backdated-missing_event_date)
    unmapped = set(rng.sample(available, 18))
    mismatch = set(rng.sample(sorted(set(available)-unmapped), 24))
    missing_intake = set(rng.sample(all_ids, 150))
    for r in referrals:
        rid = r['referral_id']
        if rid in missing_received: r['received_date']=''
        if rid in unmapped: r['source_status']='in progress?'
        if rid in mismatch: r['source_status']='closed' if current_stages[rid]!='Closed' else 'received'
        if rid in missing_intake: r['intake_owner_id']=''
    for e in events:
        rid = e['referral_id']
        if rid in backdated and e['stage_name']=='In Review':
            e['event_date'] = iso(actual_receipts[rid]-timedelta(days=2))
        if rid in missing_event_date and e['stage_name']=='Scheduled': e['event_date']=''
    # 260 repeat exports + 40 older snapshots; never deduplicate different referral IDs.
    dupe_ids = rng.sample(all_ids, 300)
    by_id = {r['referral_id']: r for r in referrals}
    for i, rid in enumerate(dupe_ids):
        copied = dict(by_id[rid])
        copied['source_row_id']=f'ROW{6001+i:07}'
        if i < 40:
            copied['source_status']='received'
            copied['source_updated_at']=iso(AS_OF-timedelta(days=1))+' 12:00:00'
        copied['ingested_at']=iso(AS_OF)+' 19:00:00'
        referrals.append(copied)
    rng.shuffle(referrals)
    activities=[]
    for i in range(1, 3601):
        account=rng.choice(accounts)
        day=rng.choice(date_pool)
        # Six intentionally neglected accounts: no touches in the most recent 60 days.
        if account['account_id'] in {'ACC010','ACC030','ACC050','ACC070','ACC090','ACC110'}:
            day=min(day, AS_OF-timedelta(days=70))
        activities.append(dict(activity_id=f'ACT{i:06}', account_id=account['account_id'],
            sales_rep_id=account['sales_rep_id'], activity_date=iso(day),
            activity_type=rng.choice(['Provider education','Phone check-in','Email follow-up','Office visit']),
            outcome=rng.choice(['Connected','Left message','Materials delivered','Follow-up requested'])))
    months=[date(2025+i//12, i%12+1, 1) for i in range(20)]
    targets=[dict(month_start=iso(m), territory_id=t['territory_id'],
                  referral_target=round((42+i*1.1)*(1.1 if t['territory_id'] in ['T03','T06'] else 1.0)))
             for i,m in enumerate(months) for t in territories]
    mappings=[]
    for canonical, aliases in synonyms.items():
        for alias in sorted(set(x.strip().lower() for x in aliases)):
            mappings.append(dict(status_key=alias, standard_status=canonical))
    config=[dict(as_of_date=iso(AS_OF), source_start_date=iso(START), cohort_days=30,
                 followup_target_calendar_days=2, stalled_stage_calendar_days=7, random_seed=SEED)]
    tables=dict(territories=territories,sites=sites,sales_reps=reps,intake_owners=owners,
                accounts=accounts,referral_rows=referrals,stage_events=events,followups=followups,
                activities=activities,targets=targets,status_map=mappings,project_config=config)
    for name, rows in tables.items(): write_csv(name, rows)
    truth=dict(seed=SEED, as_of_date=iso(AS_OF), source_start_date=iso(START),
        expected_unique_referrals=N, expected_raw_rows=len(referrals),
        duplicate_referral_ids=sorted(dupe_ids), missing_received=sorted(missing_received),
        backdated_stage=sorted(backdated), missing_stage_date=sorted(missing_event_date),
        unmapped_status=sorted(unmapped), mismatched_status=sorted(mismatch),
        missing_intake=sorted(missing_intake), source_row_counts={k:len(v) for k,v in tables.items()})
    (ROOT/'tests'/'generation_manifest.json').write_text(json.dumps(truth, indent=2)+'\n', encoding='utf-8')
    print(f'Generated {N:,} unique synthetic referrals; {len(referrals):,} source rows.')

if __name__=='__main__':
    generate()
