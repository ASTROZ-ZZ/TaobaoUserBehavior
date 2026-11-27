#!/usr/bin/env python3
"""Export objects excluded from conversion ranking because their complete follow-up sample is too small."""
from pathlib import Path
import gzip
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def main():
 for grain in ['item_id','category_id']:
  total=0;target=R/f'06_items/{grain}_insufficient_sample.csv.gz'
  with gzip.open(target,'wt',encoding='utf-8',compresslevel=1) as out:
   first=True
   for t in pd.read_csv(ROOT/f'data/processed/{grain}_metrics.csv.gz',usecols=[grain,'pv_uv','eligible_pairs','converted_pairs','conversion_rate'],chunksize=500000):
    t=t[t.eligible_pairs.fillna(0)<100].copy();t['reason']='fewer_than_100_complete_browse_onsets';total+=len(t);t.to_csv(out,index=False,header=first);first=False
  print(grain,'excluded objects',total,flush=True)
if __name__=='__main__':main()
