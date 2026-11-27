#!/usr/bin/env python3
"""Supplement segment/category browsing preference from the cleaned event stream.
Uses event counts (additive across arbitrary CSV chunks), not summed partial distinct users.
"""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def main():
 u=pd.read_csv(ROOT/'data/processed/users.csv.gz',usecols=['user_id','segment','pv','fav','cart','buy','active_days','purchase_days','category_count','buy_items']);mapping=u.set_index('user_id').segment
 profile=u.loc[u.purchase_days>=3,['pv','fav','cart','buy','active_days','purchase_days','category_count','buy_items']].describe().T.reset_index().rename(columns={'index':'feature'})
 profile.to_csv(R/'05_users/high_frequency_profile.csv',index=False,encoding='utf-8-sig')
 totals=[]
 for t in pd.read_csv(ROOT/'data/processed/events_clean.csv.gz',usecols=['user_id','category_id','behavior_type'],chunksize=2000000):
  t=t[t.behavior_type.eq('pv')].copy();t['segment']=t.user_id.map(mapping);assert t.segment.notna().all()
  totals.append(t.groupby(['segment','category_id']).size().rename('pv').reset_index())
 x=pd.concat(totals).groupby(['segment','category_id'],as_index=False).pv.sum();x['segment_pv_share']=x.pv/x.groupby('segment').pv.transform('sum')
 whole=x.groupby('category_id').pv.sum();x['overall_pv_share']=x.category_id.map(whole)/whole.sum();x['preference_lift']=x.segment_pv_share/x.overall_pv_share
 x.to_csv(R/'05_users/segment_category_preferences.csv',index=False,encoding='utf-8-sig')
 top=x.sort_values(['segment','pv'],ascending=[True,False]).groupby('segment').head(10);top.to_csv(R/'05_users/segment_top_categories.csv',index=False,encoding='utf-8-sig')
 print('Segment category preferences complete:',len(x),'segment/category combinations')
if __name__=='__main__':main()
