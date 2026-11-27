#!/usr/bin/env python3
"""Independent raw-file quality audit; can recover the final quality export without rerunning analyses."""
from pathlib import Path
import hashlib,json,platform,sys,time
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';COLS=['user_id','item_id','category_id','behavior_type','timestamp'];B=['pv','fav','cart','buy'];START=1511539200;END=1512316800

def main():
 begin=time.time();source=ROOT/'data/raw/UserBehavior.csv';sha=hashlib.sha256();lines=0
 with source.open('rb') as f:
  for z in iter(lambda:f.read(8*1024*1024),b''):sha.update(z);lines+=z.count(b'\n')
 with source.open('rb') as f:f.seek(-1,2);lines+=int(f.read(1)!=b'\n')
 counts={'raw_rows':0,'invalid_fields':0,'outside_window':0,'clean_rows':0,'exact_duplicate_excess':0,'same_second_multi_behavior_pairs':0,'raw_timestamp_min':None,'raw_timestamp_max':None};bh={};dup={b:0 for b in B};main={b:0 for b in B};examples=[];seen=set();carry=None
 def process(t):
  ids=t.user_id.unique();assert not seen.intersection(ids),'noncontiguous user blocks';seen.update(ids)
  counts['raw_rows']+=len(t)
  lo=int(t.timestamp.min());hi=int(t.timestamp.max());counts['raw_timestamp_min']=lo if counts['raw_timestamp_min'] is None else min(lo,counts['raw_timestamp_min']);counts['raw_timestamp_max']=hi if counts['raw_timestamp_max'] is None else max(hi,counts['raw_timestamp_max'])
  for k,v in t.behavior_type.value_counts().items():bh[str(k)]=bh.get(str(k),0)+int(v)
  valid=t[COLS].notna().all(axis=1)&t.behavior_type.isin(B)&(t.user_id>0)&(t.item_id>0)&(t.category_id>0)
  counts['invalid_fields']+=int((~valid).sum());win=t.timestamp.ge(START)&t.timestamp.lt(END);counts['outside_window']+=int((valid&~win).sum())
  if len(examples)<30:examples.extend(t.loc[~valid|~win].head(30-len(examples)).astype({'behavior_type':'string'}).to_dict('records'))
  e=t.loc[valid&win].copy();counts['clean_rows']+=len(e);d=e.duplicated(COLS);counts['exact_duplicate_excess']+=int(d.sum())
  for k,v in e.behavior_type.value_counts().items():main[str(k)]+=int(v)
  for k,v in e.loc[d].behavior_type.value_counts().items():dup[str(k)]+=int(v)
  # Equivalent collision audit: identical pair/timestamp with multiple behavior types.
  collisions=e[['user_id','item_id','timestamp','behavior_type']].drop_duplicates()
  counts['same_second_multi_behavior_pairs']+=int((collisions.groupby(['user_id','item_id','timestamp'],sort=False,observed=True).size()>1).sum())
 for i,t in enumerate(pd.read_csv(source,names=COLS,header=None,dtype={'user_id':'int64','item_id':'int64','category_id':'int64','timestamp':'int64','behavior_type':'category'},chunksize=2000000,on_bad_lines='error')):
  if carry is not None:t=pd.concat([carry,t],ignore_index=True)
  last=t.user_id.iloc[-1];cut=np.flatnonzero(t.user_id.to_numpy()==last)[0];carry=t.iloc[cut:].copy();t=t.iloc[:cut]
  if len(t):process(t)
  if (i+1)%5==0:print('Quality re-audit:',format(counts['raw_rows'],','),'rows',flush=True)
 if carry is not None and len(carry):process(carry)
 assert counts['raw_rows']==lines
 assert counts['raw_rows']==counts['clean_rows']+counts['outside_window']+counts['invalid_fields']
 o=pd.read_csv(R/'02_overview/overview.csv').iloc[0];assert counts['clean_rows']==int(o.events);assert main['pv']==int(o.pv);assert main['buy']==int(o.buy_events)
 mapping=pd.read_csv(R/'01_data_quality/multiple_category_items.csv');users=pd.read_csv(ROOT/'data/processed/users.csv.gz',usecols=['active_days','user_id'])
 counts.update({'file_bytes':source.stat().st_size,'sha256':sha.hexdigest(),'timezone':'Asia/Shanghai','analysis_start_inclusive':'2017-11-25 00:00:00','analysis_end_exclusive':'2017-12-04 00:00:00','unique_users':len(users),'raw_unique_users':len(seen),'user_blocks_contiguous':True,'main_duplicate_policy':'retain; distinct-user and binary path metrics unchanged by exact deduplication','items_with_multiple_categories':len(mapping),'active_days_threshold':int(users.active_days.median()),'high_purchase_days_threshold':2,'high_frequency_purchase_days_threshold':3,'quality_audit_elapsed_seconds':time.time()-begin,'quality_audit_method':'independent second full raw-file scan; strict numeric CSV parse','python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'platform':platform.platform()})
 pd.DataFrame([{'behavior':b,'duplicate_excess':dup[b],'main_events':main[b],'deduplicated_events':main[b]-dup[b],'relative_change':dup[b]/main[b]} for b in B]).to_csv(R/'01_data_quality/duplicate_sensitivity.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame([{'behavior':k,'raw_rows':v} for k,v in bh.items()]).to_csv(R/'01_data_quality/raw_behavior_values.csv',index=False,encoding='utf-8-sig');pd.DataFrame(examples).to_csv(R/'01_data_quality/excluded_examples.csv',index=False,encoding='utf-8-sig')
 (R/'01_data_quality/quality.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2));print(json.dumps(counts,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
