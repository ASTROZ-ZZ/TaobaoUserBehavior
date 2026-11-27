#!/usr/bin/env python3
"""Independent data reconciliation and small raw-history audits, no network required."""
from pathlib import Path
import json,sqlite3,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def main():
 q=json.loads((R/'01_data_quality/quality.json').read_text());o=pd.read_csv(R/'02_overview/overview.csv').iloc[0];checks=[]
 def check(name,actual,expected):
  good=bool(actual==expected);checks.append({'check':name,'passed':good,'actual':str(actual),'expected':str(expected)});assert good,(name,actual,expected)
 # Independently aggregate the user-day data from disk, rather than reusing in-memory report objects.
 n=0;pv=buy=0;day_users={};day_buyers={};day_pv={}
 for t in pd.read_csv(ROOT/'data/processed/user_day.csv.gz',chunksize=200000):
  n+=len(t);pv+=int(t.pv.sum());buy+=int(t.buy.sum())
  for d,v in t.groupby('day').size().items():day_users[int(d)]=day_users.get(int(d),0)+int(v)
  for d,v in t.groupby('day').pv.sum().items():day_pv[int(d)]=day_pv.get(int(d),0)+int(v)
  for d,v in t[t.buy>0].groupby('day').size().items():day_buyers[int(d)]=day_buyers.get(int(d),0)+int(v)
 check('user-day PV vs overview',pv,int(o.pv));check('user-day buy logs vs overview',buy,int(o.buy_events))
 for row in pd.read_csv(R/'02_overview/daily.csv').itertuples():
  check(f'day{row.day} distinct active users',day_users.get(row.day,0),int(row.uv));check(f'day{row.day} buyers',day_buyers.get(row.day,0),int(row.buy_uv));check(f'day{row.day} PV',day_pv.get(row.day,0),int(row.pv))
 # Rebuild every observable cohort cell independently from the persisted user-day table.
 days=pd.read_csv(ROOT/'data/processed/user_day.csv.gz',usecols=['user_id','day'])
 days['cohort']=days.groupby('user_id').day.transform('min');days['offset']=days.day-days.cohort
 rebuilt=days.groupby(['cohort','offset']).size()
 for row in pd.read_csv(R/'05_users/cohort_retention.csv').itertuples():
  if row.cohort_day+row.offset<=8:check(f'independent cohort {row.cohort_day} D{row.offset}',int(rebuilt.get((row.cohort_day,row.offset),0)),int(row.retained_users))
 del days,rebuilt
 names=['user_id','item_id','category_id','behavior_type','timestamp'];raw=pd.read_csv(ROOT/'data/raw/UserBehavior.csv',header=None,names=names,nrows=50000)
 raw=raw[raw.user_id.ne(raw.user_id.iloc[-1])].copy();raw=raw[(raw.timestamp>=1511539200)&(raw.timestamp<1512316800)];raw['day']=(raw.timestamp-1511539200)//86400
 conn=sqlite3.connect(ROOT/'data/processed/analysis.sqlite');ids=raw.user_id.unique()[:30];expected=pd.read_sql_query('SELECT * FROM users WHERE user_id IN ('+','.join('?' for _ in ids)+')',conn,params=[int(x) for x in ids]).set_index('user_id')
 for uid in ids:
  t=raw[raw.user_id.eq(uid)];record=expected.loc[uid]
  for b in ['pv','fav','cart','buy']:check(f'raw sample user{uid} {b}',int((t.behavior_type==b).sum()),int(record[b]))
  check(f'raw sample user{uid} active days',t.day.nunique(),int(record.active_days));check(f'raw sample user{uid} buy days',t[t.behavior_type.eq('buy')].day.nunique(),int(record.purchase_days))
 # Independent SQL timestamp matching on a small sample, retained as human-reviewable audit.
 sample=raw[raw.user_id.isin(ids)].copy();sample.to_sql('audit_events',conn,index=False,if_exists='replace')
 sql='''WITH starts AS (
 SELECT user_id,item_id,behavior_type,MIN(timestamp) AS onset FROM audit_events
 WHERE behavior_type IN ('pv','cart','fav') GROUP BY user_id,item_id,behavior_type)
 SELECT s.user_id,s.item_id,s.behavior_type,s.onset,
 EXISTS(SELECT 1 FROM audit_events b WHERE b.user_id=s.user_id AND b.item_id=s.item_id
 AND b.behavior_type='buy' AND b.timestamp>s.onset AND b.timestamp<=s.onset+86400) AS converted
 FROM starts s WHERE s.onset+86400<1512316800'''
 audit=pd.read_sql_query(sql,conn);audit.to_csv(R/'08_validation/raw_sample_path_audit.csv',index=False)
 # Independent simple event scanning checks all sampled SQL path labels.
 groups={(int(u),int(i)):g for (u,i),g in sample.groupby(['user_id','item_id'])}
 for row in audit.itertuples():
  g=groups[(row.user_id,row.item_id)];ts=g[g.behavior_type.eq('buy')].timestamp
  assert int(((ts>row.onset)&(ts<=row.onset+86400)).any())==row.converted
 check('raw sample SQL paths vs direct scan',True,True)
 conn.execute('DROP TABLE audit_events');conn.commit();conn.close()
 # Tiny deterministic edge fixtures exercise strict ordering and full follow-up.
 def converted(onset,buys,horizon=86400,end=200000):return None if onset+horizon>=end else any(onset<t<=onset+horizon for t in buys)
 check('same-second event excluded',converted(100,[100]),False)
 check('24h exact endpoint included',converted(100,[86500]),True)
 check('purchase before onset excluded',converted(100,[99]),False)
 check('incomplete follow-up missing',converted(150000,[150001]),None)
 check('window ending exactly at exclusive bound censored',converted(113600,[113601]),None)
 # All exported ratios must stay in [0,1] (sample-size floor and explicit denominator already applied).
 for path,col in [('03_conversion/conversion_24h.csv','conversion_rate'),('04_time/onset_hour_conversion.csv','conversion_rate'),('05_users/cohort_retention.csv','retention_rate')]:
  t=pd.read_csv(R/path);check(path+' bounded rates',bool(t[col].dropna().between(0,1).all()),True)
 out=pd.DataFrame(checks);out.to_csv(R/'08_validation/independent_validation.csv',index=False,encoding='utf-8-sig');print(f'Passed {len(out)} independent checks; audited {len(audit)} raw-history paths')
if __name__=='__main__':main()
