#!/usr/bin/env python3
"""Full-population, bounded-memory analysis. Requires contiguous user blocks; validates this.
Raw CSV is immutable. Processed detail and SQLite scratch support reproducibility.
"""
from pathlib import Path
import argparse, csv, gzip, hashlib, json, sqlite3, sys, time, platform
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'results'
START=int(pd.Timestamp('2017-11-25',tz='Asia/Shanghai').timestamp())
END=int(pd.Timestamp('2017-12-04',tz='Asia/Shanghai').timestamp())
KEY=['user_id','item_id']; COLS=KEY+['category_id','behavior_type','timestamp']
BHS=['pv','fav','cart','buy']
def log(s): print(time.strftime('%H:%M:%S'),s,flush=True)
def save(df,path):
 path=R/path;path.parent.mkdir(parents=True,exist_ok=True);df.to_csv(path,index=False,encoding='utf-8-sig',float_format='%.8g')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--chunk-size',type=int,default=1000000);args=ap.parse_args()
 for d in ['../data/processed','01_data_quality','02_overview','03_conversion','04_time','05_users','06_items','08_validation','../data/intermediate']:(R/d).mkdir(parents=True,exist_ok=True)
 source=ROOT/'data/raw/UserBehavior.csv'; started=time.time(); sha=hashlib.sha256();nlines=0
 with source.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):sha.update(block);nlines+=block.count(b'\n')
 with source.open('rb') as f:f.seek(-1,2);nlines+=int(f.read(1)!=b'\n')
 log(f'SHA256 complete; physical lines={nlines:,}')
 db=ROOT/'data/intermediate/aggregates.sqlite';db.unlink(missing_ok=True);conn=sqlite3.connect(db)
 conn.execute('PRAGMA journal_mode=OFF');conn.execute('PRAGMA synchronous=OFF');conn.execute('PRAGMA temp_store=FILE')
 counts={'raw_rows':0,'invalid_fields':0,'outside_window':0,'clean_rows':0,'exact_duplicate_excess':0,'same_second_multi_behavior_pairs':0,'raw_timestamp_min':None,'raw_timestamp_max':None}
 seen=set(); users=[];daily=[];hours=[];convs=[];branches=[];historical=[];waits=[];intervals=[];cohorts=[];rep=[];sens=[];duplicates=[];mappings=[]
 behavior_raw={};bad_samples=[];carry=None;part=0
 cleanout=gzip.open(ROOT/'data/processed/events_clean.csv.gz','wt',encoding='utf-8',compresslevel=1,newline='');pd.DataFrame(columns=COLS+['day','hour']).to_csv(cleanout,index=False)
 dayout=gzip.open(ROOT/'data/processed/user_day.csv.gz','wt',encoding='utf-8',compresslevel=1,newline='');dayheader=True
 def handle(raw):
  nonlocal part,dayheader
  part+=1
  # Users must not reappear in a later processed block, otherwise abort instead of silently biasing paths.
  ids=raw.user_id.dropna().unique();overlap=seen.intersection(ids)
  if overlap:raise RuntimeError(f'Noncontiguous users: {list(overlap)[:3]}; use external user sort before running')
  seen.update(ids)
  counts['raw_rows']+=len(raw)
  for b,n in raw.behavior_type.value_counts(dropna=False).items():behavior_raw[str(b)]=behavior_raw.get(str(b),0)+int(n)
  for c in ['user_id','item_id','category_id','timestamp']:raw[c]=pd.to_numeric(raw[c],errors='coerce')
  ts=raw.timestamp.dropna()
  if len(ts):
   counts['raw_timestamp_min']=float(ts.min()) if counts['raw_timestamp_min'] is None else min(counts['raw_timestamp_min'],float(ts.min()))
   counts['raw_timestamp_max']=float(ts.max()) if counts['raw_timestamp_max'] is None else max(counts['raw_timestamp_max'],float(ts.max()))
  valid=raw[COLS].notna().all(axis=1)&raw.behavior_type.isin(BHS)
  for c in ['user_id','item_id','category_id']:valid&=(raw[c]>0)&(raw[c]%1==0)
  valid&=(raw.timestamp%1==0)
  counts['invalid_fields']+=int((~valid).sum())
  window=raw.timestamp.ge(START)&raw.timestamp.lt(END)
  counts['outside_window']+=int((valid&~window).sum())
  if len(bad_samples)<30:bad_samples.extend(raw.loc[~valid|~window].head(30-len(bad_samples)).fillna('').to_dict('records'))
  e=raw.loc[valid&window].copy()
  if e.empty:return
  for c in ['user_id','item_id','category_id','timestamp']:e[c]=e[c].astype('int64')
  counts['clean_rows']+=len(e);dup=e.duplicated(COLS);counts['exact_duplicate_excess']+=int(dup.sum())
  dc=e.loc[dup].groupby('behavior_type').size();duplicates.append(dc)
  # Preserve exact repeats in the main event-count metrics; report deduplicated sensitivity.
  e['day']=((e.timestamp-START)//86400).astype('int8');e['hour']=((e.timestamp+28800)%86400//3600).astype('int8')
  e.to_csv(cleanout,index=False,header=False)
  e[['item_id','category_id']].drop_duplicates().to_sql('mapping_partial',conn,if_exists='append',index=False)
  ud=e.groupby(['user_id','day','behavior_type'],observed=True).size().unstack(fill_value=0).reindex(columns=BHS,fill_value=0).reset_index()
  ud.to_csv(dayout,index=False,header=dayheader);dayheader=False
  u=ud.groupby('user_id')[BHS].sum();u['active_days']=ud.groupby('user_id').size();u['purchase_days']=ud.loc[ud.buy>0].groupby('user_id').size().reindex(u.index,fill_value=0)
  u['first_day']=ud.groupby('user_id').day.min();u['last_day']=ud.groupby('user_id').day.max()
  u['category_count']=e.groupby('user_id').category_id.nunique();u['buy_items']=e.loc[e.behavior_type.eq('buy')].groupby('user_id').item_id.nunique().reindex(u.index,fill_value=0)
  u['first_buy_day']=ud.loc[ud.buy>0].groupby('user_id').day.min().reindex(u.index)
  users.append(u.reset_index())
  for keys,arr in [(['day'],daily),(['day','hour'],hours)]:
   # Full user blocks ensure sum of batch distinct user counts is exact.
   g=e.groupby(keys,observed=True);t=g.size().rename('events').to_frame();t['uv']=g.user_id.nunique()
   for bh in BHS:
    sub=e[e.behavior_type.eq(bh)].groupby(keys,observed=True);t[bh]=sub.size();t[bh+'_uv']=sub.user_id.nunique()
   arr.append(t.fillna(0).reset_index())
  for grain in ['item_id','category_id']:
   g=e.groupby(grain,observed=True);t=g.size().rename('events').to_frame();t['uv']=g.user_id.nunique()
   for bh in BHS:
    sub=e[e.behavior_type.eq(bh)].groupby(grain,observed=True);t[bh]=sub.size();t[bh+'_uv']=sub.user_id.nunique()
   t.fillna(0).reset_index().to_sql(grain+'_partial',conn,if_exists='append',index=False)
  itemday=e.groupby(['item_id','day','behavior_type'],observed=True).size().unstack(fill_value=0).reindex(columns=BHS,fill_value=0).reset_index();itemday.to_sql('item_day_partial',conn,if_exists='append',index=False)
  first=ud.groupby('user_id').day.min();ud['cohort']=ud.user_id.map(first);ud['offset']=ud.day-ud.cohort
  cohorts.append(ud.groupby(['cohort','offset']).size().rename('users').reset_index())
  buys=e[e.behavior_type.eq('buy')]
  bd=buys.groupby(['user_id','day']).timestamp.min().reset_index().sort_values(['user_id','day'])
  bd['interval_hours']=bd.groupby('user_id').timestamp.diff()/3600
  intervals.append(bd.loc[bd.interval_hours.notna(),['user_id','interval_hours']])
  # Equal 3-day follow-up based on first observed purchase day.
  if len(bd):
   bd['first']=bd.groupby('user_id').day.transform('min');eligible=bd[bd['first']<=5]
   rr=eligible.assign(again=(eligible.day>eligible['first'])&(eligible.day<=eligible['first']+3)).groupby('user_id').agg(first=('first','first'),again=('again','max'))
   rep.append(rr.groupby('first').agg(users=('again','size'),repeat_users=('again','sum')).reset_index())
  starts=e.groupby(KEY+['behavior_type'],observed=True).timestamp.min().unstack().reindex(columns=BHS).reset_index()
  starts['category_id']=e.groupby(KEY).category_id.first().to_numpy()
  # Same timestamp does not establish event ordering.
  collisions=e.groupby(KEY+['timestamp']).behavior_type.nunique();counts['same_second_multi_behavior_pairs']+=int((collisions>1).sum())
  buy=buys[KEY+['timestamp']].rename(columns={'timestamp':'bt'})
  for bh in ['pv','cart','fav']:
   s=starts.loc[starts[bh].notna(),KEY+['category_id',bh]].rename(columns={bh:'onset'})
   s['onset']=s.onset.astype('int64')
   m=s.merge(buy,on=KEY,how='inner');m=m[(m.bt>m.onset)&(m.bt<=m.onset+172800)]
   bt=m.groupby(KEY).bt.min().rename('next_buy');s=s.join(bt,on=KEY)
   s['delay']=s.next_buy-s.onset;s['day']=((s.onset-START)//86400).astype('int8');s['hour']=((s.onset+28800)%86400//3600).astype('int8')
   # Conservative histories: strictly preceding natural days; same-day earlier events excluded.
   hist=ud[['user_id','day','pv','buy']].copy();hist['prior_active_days']=hist.groupby('user_id').cumcount();hist['prior_buys']=hist.groupby('user_id').buy.cumsum()-hist.buy
   s=s.merge(hist[['user_id','day','prior_active_days','prior_buys']],on=['user_id','day'],how='left',validate='many_to_one')
   s['history_group']=np.where(s.prior_active_days>=3,'prior_active_3plus','prior_active_0to2')
   for horizon in [3600,86400,172800]:
    q=s[s.onset+horizon<END].copy();q['converted']=q.delay.le(horizon)&q.delay.gt(0)
    sens.append({'behavior':bh,'hours':horizon/3600,'eligible_pairs':len(q),'converted_pairs':int(q.converted.sum())})
   q=s[s.onset+86400<END].copy();q['converted']=q.delay.le(86400)&q.delay.gt(0)
   convs.append({'behavior':bh,'eligible_pairs':len(q),'converted_pairs':int(q.converted.sum()),'censored_pairs':len(s)-len(q)})
   historical.append(q.groupby(['history_group']).agg(eligible_pairs=('converted','size'),converted_pairs=('converted','sum')).reset_index().assign(behavior=bh))
   cat=q.groupby('category_id').agg(eligible_pairs=('converted','size'),converted_pairs=('converted','sum')).reset_index().assign(behavior=bh);cat.to_sql('category_conversion_partial',conn,if_exists='append',index=False)
   waits.append(q.loc[q.converted,['delay']].assign(behavior=bh))
   if bh=='pv':
    for key,table in [('item_id','item_conversion_partial'),('hour','hour_conversion_partial')]:q.groupby(key).agg(eligible_pairs=('converted','size'),converted_pairs=('converted','sum')).reset_index().to_sql(table,conn,if_exists='append',index=False)
    # first qualifying intermediate after the first browse, then first purchase strictly after it.
    flags={};midtimes={}
    for mid in ['cart','fav']:
     mm=q[KEY+['onset']].merge(e.loc[e.behavior_type.eq(mid),KEY+['timestamp']],on=KEY)
     mm=mm[(mm.timestamp>mm.onset)&(mm.timestamp<=mm.onset+86400)]
     ft=mm.groupby(KEY).timestamp.min().rename('midtime');qq=q.join(ft,on=KEY)
     zz=qq.loc[qq.midtime.notna(),KEY+['onset','midtime']].merge(buy,on=KEY)
     zz=zz[(zz.bt>zz.midtime)&(zz.bt<=zz.onset+86400)]
     success=zz[KEY].drop_duplicates();success['success']=True
     qq=qq.merge(success,on=KEY,how='left');qq['success']=qq.success.eq(True)
     branches.append({'path':'pv_'+mid+'_buy','start_pairs':len(qq),'middle_pairs':int(qq.midtime.notna().sum()),'purchase_pairs':int(qq.success.sum())})
     flags[mid]=qq.success.to_numpy();midtimes[mid]=qq.midtime.to_numpy()
    # Earliest qualifying purchase after browse. For direct path, no observed intermediate before it.
    direct=q.converted.to_numpy().copy()
    for mid in ['cart','fav']:direct &= ~(np.isfinite(midtimes[mid]) & (midtimes[mid]<q.next_buy.to_numpy()))
    branches.append({'path':'pv_direct_buy','start_pairs':len(q),'middle_pairs':0,'purchase_pairs':int(direct.sum())})
  log(f'block {part}: raw {counts["raw_rows"]:,}; clean {counts["clean_rows"]:,}; users {len(seen):,}')
 reader=pd.read_csv(source,header=None,names=COLS,dtype='string',chunksize=args.chunk_size,on_bad_lines='error')
 for chunk in reader:
  raw=pd.concat([carry,chunk],ignore_index=True) if carry is not None else chunk
  # Retain last entire user block to prevent boundary splits.
  last=raw.user_id.iloc[-1];mask=raw.user_id.eq(last).fillna(False);cut=np.flatnonzero(mask.to_numpy())[0]
  carry=raw.iloc[cut:].copy();batch=raw.iloc[:cut].copy()
  if len(batch):handle(batch)
 if carry is not None and len(carry):handle(carry)
 cleanout.close();dayout.close()
 assert counts['raw_rows']==nlines,'CSV physical/parsed row discrepancy'
 assert counts['raw_rows']==counts['clean_rows']+counts['outside_window']+counts['invalid_fields']
 log('Consolidating aggregate outputs')
 u=pd.concat(users,ignore_index=True);assert u.user_id.is_unique
 daily_df=pd.concat(daily).groupby('day',as_index=False).sum(numeric_only=True)
 hourly=pd.concat(hours).groupby(['day','hour'],as_index=False).sum(numeric_only=True)
 for t in [daily_df,hourly]:
  t['date']=pd.Timestamp('2017-11-25')+pd.to_timedelta(t.day,unit='D');t['purchase_rate']=t.buy_uv/t.uv;t['pv_per_browser']=t.pv/t.pv_uv
 save(daily_df,'02_overview/daily.csv');save(hourly,'04_time/date_hour.csv')
 hh=hourly.drop(columns=['date','day','purchase_rate','pv_per_browser']).groupby('hour',as_index=False).sum();hh['purchase_rate']=hh.buy_uv/hh.uv
 save(hh,'04_time/hour_summary.csv')
 daily_df['day_type']=np.where(daily_df.date.dt.dayofweek>=5,'weekend','weekday')
 wd=daily_df.groupby('day_type').agg(days=('day','size'),pv=('pv','sum'),uv_user_days=('uv','sum'),buy_uv_user_days=('buy_uv','sum'));wd['daily_pv']=wd.pv/wd.days;wd['daily_uv']=wd.uv_user_days/wd.days;wd['purchase_rate']=wd.buy_uv_user_days/wd.uv_user_days;save(wd.reset_index(),'04_time/weekday_weekend.csv')
 overview={'events':counts['clean_rows'],'uv':len(u),'pv':int(u.pv.sum()),'pv_uv':int((u.pv>0).sum()),'fav_uv':int((u.fav>0).sum()),'cart_uv':int((u.cart>0).sum()),'buy_uv':int((u.buy>0).sum()),'buy_events':int(u.buy.sum())};overview['purchase_rate']=overview['buy_uv']/overview['uv'];overview['pv_per_browser']=overview['pv']/overview['pv_uv']
 save(pd.DataFrame([overview]),'02_overview/overview.csv')
 coverage=[]
 for a in BHS:
  for b in BHS:coverage.append({'behavior_a':a,'behavior_b':b,'users':int(((u[a]>0)&(u[b]>0)).sum())})
 save(pd.DataFrame(coverage),'03_conversion/user_behavior_intersections.csv')
 uvpatterns=u.groupby([u.fav.gt(0).rename('has_fav'),u.cart.gt(0).rename('has_cart')]).agg(users=('user_id','size'),buyers=('buy',lambda x:(x>0).sum())).reset_index();uvpatterns['purchase_rate']=uvpatterns.buyers/uvpatterns.users;save(uvpatterns,'03_conversion/fav_cart_coverage.csv')
 cv=pd.DataFrame(convs).groupby('behavior',as_index=False).sum();cv['conversion_rate']=cv.converted_pairs/cv.eligible_pairs;cv['unconverted_pairs']=cv.eligible_pairs-cv.converted_pairs;save(cv,'03_conversion/conversion_24h.csv')
 br=pd.DataFrame(branches).groupby('path',as_index=False).sum();br['start_to_buy_rate']=br.purchase_pairs/br.start_pairs;br['middle_to_buy_rate']=br.purchase_pairs/br.middle_pairs.replace(0,np.nan);save(br,'03_conversion/branch_funnel.csv')
 se=pd.DataFrame(sens).groupby(['behavior','hours'],as_index=False).sum();se['conversion_rate']=se.converted_pairs/se.eligible_pairs;save(se,'03_conversion/window_sensitivity.csv')
 hg=pd.concat(historical).groupby(['behavior','history_group'],as_index=False).sum();hg['conversion_rate']=hg.converted_pairs/hg.eligible_pairs;save(hg,'03_conversion/historical_segments.csv')
 w=pd.concat(waits,ignore_index=True);ws=w.groupby('behavior').delay.agg(['size','mean','median',lambda x:x.quantile(.25),lambda x:x.quantile(.75)]).reset_index();ws.columns=['behavior','pairs','mean_seconds','median_seconds','p25_seconds','p75_seconds'];save(ws,'03_conversion/converted_waiting_time.csv')
 ct=pd.concat(cohorts).groupby(['cohort','offset'],as_index=False).users.sum();base=ct.loc[ct.offset.eq(0)].set_index('cohort').users
 rows=[]
 for d in range(9):
  for k in range(9):
   eligible=d+k<=8;matches=ct[(ct.cohort==d)&(ct.offset==k)];n=int(matches.users.sum()) if eligible else np.nan;den=int(base.get(d,0));rows.append({'cohort_day':d,'cohort_date':str((pd.Timestamp('2017-11-25')+pd.Timedelta(days=d)).date()),'offset':k,'cohort_users':den,'retained_users':n,'retention_rate':n/den if eligible and den else np.nan})
 save(pd.DataFrame(rows),'05_users/cohort_retention.csv')
 iv=pd.concat(intervals,ignore_index=True);save(iv,'../data/processed/repeat_intervals.csv.gz');st=iv.interval_hours.describe(percentiles=[.25,.5,.75]).to_dict();st['users']=iv.user_id.nunique();save(pd.DataFrame([st]),'05_users/repeat_interval_summary.csv')
 rp=pd.concat(rep).groupby('first',as_index=False).sum();rp['repeat_rate_3d']=rp.repeat_users/rp.users;save(rp,'05_users/repeat_cohort_3d.csv')
 pdist=u.groupby('purchase_days').agg(users=('user_id','size'),pv=('pv','sum'),buy_events=('buy','sum')).reset_index();save(pdist,'05_users/purchase_days_distribution.csv')
 active_threshold=int(u.active_days.median());buy_threshold=2
 u['segment']=np.where(u.active_days>=active_threshold,'高活跃','低活跃')+'＋'+np.where(u.purchase_days>=buy_threshold,'高购买','低购买')
 u['intent_group']=np.select([u.purchase_days>=2,u.purchase_days.eq(1),u.cart.gt(0),u.fav.gt(0)],['多日购买','单日购买','未购但加购','未购未加购但收藏'],default='仅浏览及其他')
 save(u,'../data/processed/users.csv.gz')
 sg=u.groupby('segment').agg(users=('user_id','size'),pv=('pv','sum'),buyers=('buy',lambda x:(x>0).sum()),mean_active_days=('active_days','mean'),mean_purchase_days=('purchase_days','mean'),fav_users=('fav',lambda x:(x>0).sum()),cart_users=('cart',lambda x:(x>0).sum()),mean_categories=('category_count','mean')).reset_index();sg['share']=sg.users/len(u);save(sg,'05_users/segments.csv')
 save(u.groupby(['segment','intent_group']).size().rename('users').reset_index(),'05_users/segment_intents.csv')
 th=[]
 for a in sorted(set([max(1,active_threshold-1),active_threshold,min(9,active_threshold+1)])):
  for b in [2,3]:
   z=np.where(u.active_days>=a,'高活跃','低活跃')+'＋'+np.where(u.purchase_days>=b,'高购买','低购买')
   for k,v in pd.Series(z).value_counts().items():th.append({'active_days_threshold':a,'purchase_days_threshold':b,'segment':k,'users':int(v)})
 save(pd.DataFrame(th),'05_users/segment_threshold_sensitivity.csv')
 save(u[u.purchase_days>=3].describe(include='number').T.reset_index().rename(columns={'index':'feature'}),'05_users/high_frequency_profile.csv')
 # Consolidate SQLite partials. These small/medium aggregates avoid holding all item records in memory.
 def aggregate(table,keys,values):
  sql='SELECT '+','.join(keys)+','+','.join('SUM('+v+') AS '+v for v in values)+' FROM '+table+' GROUP BY '+','.join(keys)
  return pd.read_sql_query(sql,conn)
 vals=['events','uv']+[v for bh in BHS for v in [bh,bh+'_uv']]
 ic=aggregate('item_conversion_partial',['item_id'],['eligible_pairs','converted_pairs']);ic['conversion_rate']=ic.converted_pairs/ic.eligible_pairs
 hc=aggregate('hour_conversion_partial',['hour'],['eligible_pairs','converted_pairs']);hc['conversion_rate']=hc.converted_pairs/hc.eligible_pairs;save(hc,'04_time/onset_hour_conversion.csv')
 cc=aggregate('category_conversion_partial',['category_id','behavior'],['eligible_pairs','converted_pairs']);cc['conversion_rate']=cc.converted_pairs/cc.eligible_pairs;save(cc,'03_conversion/category_conversion.csv')
 mapping=pd.read_sql_query('SELECT item_id,COUNT(DISTINCT category_id) AS category_count FROM mapping_partial GROUP BY item_id',conn);counts['items_with_multiple_categories']=int((mapping.category_count>1).sum());save(mapping[mapping.category_count>1],'01_data_quality/multiple_category_items.csv')
 for grain in ['item_id','category_id']:
  t=aggregate(grain+'_partial',[grain],vals)
  cc2=ic if grain=='item_id' else cc[cc.behavior.eq('pv')].drop(columns='behavior')
  t=t.merge(cc2,on=grain,how='left');t['conversion_rate']=t.converted_pairs/t.eligible_pairs
  t.to_csv(ROOT/f'data/processed/{grain}_metrics.csv.gz',index=False,compression='gzip')
  for metric in ['pv','pv_uv','buy_uv']:save(t.nlargest(30,metric),f'06_items/top_{grain}_{metric}.csv')
  eligible=t[t.eligible_pairs>=100].copy();traffic=float(eligible.pv_uv.quantile(.75));rate=float(eligible.conversion_rate.median())
  eligible['quadrant']=np.where(eligible.pv_uv>=traffic,'高流量','低流量')+'＋'+np.where(eligible.conversion_rate>=rate,'高转化','低转化')
  save(eligible.nlargest(50,'conversion_rate'),f'06_items/top_{grain}_conversion.csv')
  for quadrant in ['高流量＋低转化','低流量＋高转化']:
   x=eligible[eligible.quadrant.eq(quadrant)];x=x.sort_values(['pv_uv' if quadrant.startswith('高') else 'conversion_rate'],ascending=False)
   save(x.head(100),f'06_items/{grain}_{"high_traffic_low_conversion" if quadrant.startswith("高") else "low_traffic_high_conversion"}.csv')
  save(eligible.groupby('quadrant').agg(objects=(grain,'size'),browse_user_objects=('pv_uv','sum'),eligible_pairs=('eligible_pairs','sum'),converted_pairs=('converted_pairs','sum')).reset_index(),f'06_items/{grain}_quadrants.csv')
  save(eligible.sample(n=min(20000,len(eligible)),random_state=42),f'06_items/{grain}_scatter_sample.csv')
  checks=[]
  for minimum in [50,100,200]:
   zz=t[t.eligible_pairs>=minimum];top=zz.nlargest(30,'conversion_rate');checks.append({'minimum_pairs':minimum,'objects':len(zz),'median_conversion':zz.conversion_rate.median(),'top30_mean_conversion':top.conversion_rate.mean(),'top30_overlap_with_min100':len(set(top[grain])&set(eligible.nlargest(30,'conversion_rate')[grain]))})
  save(pd.DataFrame(checks),f'06_items/{grain}_threshold_sensitivity.csv')
  save(pd.DataFrame([{'minimum_pairs':100,'traffic_p75':traffic,'conversion_median':rate,'eligible_objects':len(eligible),'all_objects':len(t),'top10_pv_share':t.nlargest(10,'pv').pv.sum()/t.pv.sum(),'top100_pv_share':t.nlargest(100,'pv').pv.sum()/t.pv.sum()}]),f'06_items/{grain}_thresholds.csv')
 log('Writing item-day aggregates')
 # Stream grouped SQLite query to compressed CSV.
 sql='SELECT item_id,day,'+','.join('SUM('+x+') AS '+x for x in BHS)+' FROM item_day_partial GROUP BY item_id,day'
 with gzip.open(ROOT/'data/processed/item_day.csv.gz','wt',encoding='utf-8',compresslevel=1) as out:
  first=True
  for df in pd.read_sql_query(sql,conn,chunksize=500000):df.to_csv(out,index=False,header=first);first=False
 du=pd.concat(duplicates,axis=1).fillna(0).sum(axis=1).rename('duplicate_excess').reindex(BHS,fill_value=0).rename_axis('behavior').reset_index()
 du['main_events']=[int(u[b].sum()) for b in du.behavior];du['deduplicated_events']=du.main_events-du.duplicate_excess;du['relative_change']=du.duplicate_excess/du.main_events;save(du,'01_data_quality/duplicate_sensitivity.csv')
 save(pd.DataFrame([{'behavior':k,'raw_rows':v} for k,v in behavior_raw.items()]),'01_data_quality/raw_behavior_values.csv');save(pd.DataFrame(bad_samples),'01_data_quality/excluded_examples.csv')
 counts.update({'file_bytes':source.stat().st_size,'sha256':sha.hexdigest(),'timezone':'Asia/Shanghai','analysis_start_inclusive':'2017-11-25 00:00:00','analysis_end_exclusive':'2017-12-04 00:00:00','unique_users':len(u),'user_blocks_contiguous':True,'main_duplicate_policy':'retain; distinct-user and binary path metrics unchanged by exact deduplication','active_days_threshold':active_threshold,'high_purchase_days_threshold':buy_threshold,'high_frequency_purchase_days_threshold':3,'elapsed_seconds':time.time()-started,'python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'platform':platform.platform()})
 (R/'01_data_quality/quality.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2))
 conn.close();log('Analysis complete '+json.dumps(overview));log(f'elapsed {time.time()-started:.1f}s')
if __name__=='__main__':main()
