#!/usr/bin/env python3
"""Export concrete audience and SKU worklists from verified processed data."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';O=R/'10_operating_lists'
def main():
 O.mkdir(parents=True,exist_ok=True)
 target=[];single=[]
 for df in pd.read_csv(ROOT/'data/processed/users.csv.gz',chunksize=200000):
  high=df[df.segment.eq('高活跃＋低购买')]
  target.append(high[(high.buy==0)&(high.cart>0)])
  single.append(high[high.purchase_days.eq(1)])
 cols=['user_id','active_days','purchase_days','pv','fav','cart','buy','category_count','segment','intent_group']
 for name,parts,expected in [('priority_cart_audience',target,117340),('single_purchase_audience',single,185159)]:
  result=pd.concat(parts,ignore_index=True)[cols].sort_values(['active_days','cart','pv'],ascending=False)
  assert len(result)==expected and result.user_id.nunique()==expected
  result.to_csv(O/(name+'.csv'),index=False,encoding='utf-8-sig')
  print(name,len(result))
 sku=pd.read_csv(R/'06_items/item_id_high_traffic_low_conversion.csv');assert len(sku)==100
 sku.insert(0,'priority',range(1,101));sku['next_action']='可售与库存核查；详情与需求匹配；渠道与人群对照'
 sku.to_csv(O/'priority_product_worklist.csv',index=False,encoding='utf-8-sig')
 (O/'README.md').write_text('''# 运营对象清单

- priority_cart_audience.csv：117,340名高活跃、期间未购买且发生加购的用户。
- single_purchase_audience.csv：185,159名高活跃、仅一个自然日发生购买的用户。
- priority_product_worklist.csv：100个高流量低转化商品与核查动作。

用户表含匿名用户ID、活跃天数、购买天数、浏览/收藏/加购/购买次数、品类覆盖及分层标签。人群为九天窗口内画像；用于后续运营时应更新近期购买、可售、触达资格和频控。商品排序沿用高流量低转化候选文件。
''',encoding='utf-8')
if __name__=='__main__':main()
