#!/usr/bin/env python3
"""Derive operational priorities and recruiter-facing evidence charts from verified results."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';O=R/'07_decision_support';A=R/'09_report_charts'
os.environ['MPLCONFIGDIR']=str(ROOT/'data/intermediate/matplotlib')
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
for f in ['/System/Library/Fonts/Supplemental/Songti.ttc','/System/Library/Fonts/Supplemental/Times New Roman.ttf']:fontManager.addfont(f)
plt.rcParams.update({'font.family':['Times New Roman','Songti SC','DejaVu Sans'],'axes.unicode_minus':False,'font.size':12,'axes.titlesize':15,'axes.titleweight':'bold','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':'#E8ECF1','axes.axisbelow':True,'savefig.dpi':300,'figure.facecolor':'white','axes.facecolor':'white'})
C=['#22577A','#38A3A5','#D88C43','#B75252'];G='#6D7D8D'
def read(p):return pd.read_csv(R/p)
def out(fig,name):fig.tight_layout();fig.savefig(A/(name+'.png'),dpi=300,bbox_inches='tight');plt.close(fig)
def main():
 O.mkdir(parents=True,exist_ok=True);A.mkdir(parents=True,exist_ok=True)
 o=read('02_overview/overview.csv').iloc[0];d=read('02_overview/daily.csv');cv=read('03_conversion/conversion_24h.csv').set_index('behavior');sg=read('05_users/segments.csv');it=read('05_users/segment_intents.csv');pdst=read('05_users/purchase_days_distribution.csv');qu=read('06_items/item_id_quadrants.csv');goods=read('06_items/item_id_thresholds.csv').iloc[0];wd=read('04_time/weekday_weekend.csv').set_index('day_type');focus=it[it.segment.eq('高活跃＋低购买')];op=read('06_items/item_id_high_traffic_low_conversion.csv')
 stats={'dau_growth':float(d.iloc[7].uv/d.iloc[0].uv-1),'buyers_growth':float(d.iloc[7].buy_uv/d.iloc[0].buy_uv-1),'purchase_rate_change_pp':float((d.iloc[7].purchase_rate-d.iloc[0].purchase_rate)*100),'cart_to_browse_rate_ratio':float(cv.loc['cart','conversion_rate']/cv.loc['pv','conversion_rate']),'fav_to_browse_rate_ratio':float(cv.loc['fav','conversion_rate']/cv.loc['pv','conversion_rate']),'weekend_pv_growth':float(wd.loc['weekend','daily_pv']/wd.loc['weekday','daily_pv']-1),'weekend_buyer_growth':float((wd.loc['weekend','buy_uv_user_days']/wd.loc['weekend','days'])/(wd.loc['weekday','buy_uv_user_days']/wd.loc['weekday','days'])-1),'weekend_rate_diff_pp':float((wd.loc['weekend','purchase_rate']-wd.loc['weekday','purchase_rate'])*100),'high_active_user_share':float(sg[sg.segment.str.startswith('高活跃')].users.sum()/o.uv),'high_active_pv_share':float(sg[sg.segment.str.startswith('高活跃')].pv.sum()/o.pv),'high_active_low_pv_share':float(sg[sg.segment.eq('高活跃＋低购买')].pv.sum()/o.pv),'high_active_nonbuyers':int(focus[focus.intent_group.ne('单日购买')].users.sum()),'cart_focus_users':117340,'cart_focus_share_nonbuyers':float(117340/focus[focus.intent_group.ne('单日购买')].users.sum()),'high_frequency_users':int(pdst[pdst.purchase_days>=3].users.sum()),'high_frequency_buyer_share':float(pdst[pdst.purchase_days>=3].users.sum()/o.buy_uv),'high_frequency_buy_log_share':float(pdst[pdst.purchase_days>=3].buy_events.sum()/o.buy_events),'eligible_sku_share':float(goods.eligible_objects/goods.all_objects),'eligible_browse_coverage':float(qu.eligible_pairs.sum()/cv.loc['pv','eligible_pairs']),'eligible_conversion_coverage':float(qu.converted_pairs.sum()/cv.loc['pv','converted_pairs'])}
 qu['browse_share']=qu.eligible_pairs/qu.eligible_pairs.sum();qu['conversion_share']=qu.converted_pairs/qu.converted_pairs.sum();qu['weighted_rate']=qu.converted_pairs/qu.eligible_pairs
 lo=qu[qu.quadrant.eq('高流量＋低转化')].iloc[0];hi=qu[qu.quadrant.eq('高流量＋高转化')].iloc[0]
 stats.update({'low_efficiency_skus':int(lo.objects),'low_efficiency_observations':int(lo.eligible_pairs),'low_efficiency_browse_share':float(lo.browse_share),'low_efficiency_conversion_share':float(lo.conversion_share),'low_efficiency_rate':float(lo.weighted_rate),'high_efficiency_rate':float(hi.weighted_rate),'high_to_low_efficiency_ratio':float(hi.weighted_rate/lo.weighted_rate),'candidate_skus':len(op),'candidate_top10_observations':int(op.head(10).eligible_pairs.sum()),'candidate_top10_conversions':int(op.head(10).converted_pairs.sum())})
 qu.to_csv(O/'business_product_quadrants.csv',index=False,encoding='utf-8-sig');(O/'business_findings.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
 fig,ax=plt.subplots(figsize=(10,4.7));x=np.arange(9);ax.plot(x,d.uv/d.iloc[0].uv*100,'o-',label='活跃用户指数',color=C[0],lw=2.1);ax.plot(x,d.buy_uv/d.iloc[0].buy_uv*100,'o-',label='购买用户指数',color=C[1],lw=2.1);ax.set_xticks(x,[v[5:] for v in d.date]);ax.set(title='活跃扩张与购买用户增长的匹配程度',ylabel='指数  11月25日=100');ax.legend();out(fig,'biz_growth_quality')
 fig,ax=plt.subplots(figsize=(9,4.7));cover=[float(o.pv_uv),float(o.cart_uv),float(o.fav_uv),float(o.buy_uv)];labels=['浏览','加购','收藏','购买'];ax.bar(labels,np.array(cover)/1e4,color=C)
 for i,v in enumerate(cover):ax.text(i,v/1e4+1,f'{v/o.uv:.1%}',ha='center',fontsize=12)
 ax.set(title='用户行为覆盖与运营触点',ylabel='万用户',ylim=(0,110));out(fig,'biz_behavior_coverage')
 fig,ax=plt.subplots(figsize=(9,4.8));order=['pv','fav','cart'];vals=[cv.loc[b,'conversion_rate'] for b in order];ax.bar(['浏览','收藏','加购'],vals,color=[C[0],C[2],C[1]])
 for i,v in enumerate(vals):ax.text(i,v+.0012,f'{v:.2%}',ha='center',fontsize=16)
 ax.set(title='意向行为后的购买转化表现',ylabel='24小时购买率',ylim=(0,.049));ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1));out(fig,'biz_conversion')
 history=read('03_conversion/historical_segments.csv');x=history[history.behavior.eq('cart')];fig,ax=plt.subplots(figsize=(9,4.6));ax.bar(['此前活跃0—2天','此前活跃至少3天'],x.conversion_rate,color=C[:2]);ax.set(title='加购用户的历史活跃与后续转化',ylabel='24小时购买率',ylim=(0,.052));ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
 for i,v in enumerate(x.conversion_rate):ax.text(i,v+.0015,f'{v:.2%}',ha='center',fontsize=15)
 out(fig,'biz_cart_history')
 fig,ax=plt.subplots(figsize=(10,4.9));xx=np.arange(4);ax.bar(xx-.17,sg.share,.34,label='用户占比',color=C[0]);ax.bar(xx+.17,sg.pv/o.pv,.34,label='浏览量占比',color=C[2]);ax.set_xticks(xx,sg.segment,rotation=10);ax.set(title='各用户层的规模与流量贡献',ylabel='占比',ylim=(0,.5));ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1));ax.legend();out(fig,'biz_segment_value')
 fig,ax=plt.subplots(figsize=(10,4.9));purchased=pdst[pdst.purchase_days>0].copy();purchased['group']=np.where(purchased.purchase_days>=3,'购买≥3天',np.where(purchased.purchase_days.eq(2),'购买2天','购买1天'));g=purchased.groupby('group').agg(users=('users','sum'),events=('buy_events','sum')).reindex(['购买1天','购买2天','购买≥3天']);xx=np.arange(3);ax.bar(xx-.18,g.users/o.buy_uv,.36,label='购买用户占比',color=C[0]);ax.bar(xx+.18,g.events/o.buy_events,.36,label='购买行为贡献',color=C[1]);ax.set_xticks(xx,g.index);ax.set(title='高频购买客群的贡献度',ylabel='占比',ylim=(0,.65));ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1));ax.legend();out(fig,'biz_purchase_value')
 fig,ax=plt.subplots(figsize=(10,4.9));xx=np.arange(4);ax.bar(xx-.18,qu.browse_share,.36,label='转化观察量占比',color=C[0]);ax.bar(xx+.18,qu.conversion_share,.36,label='购买转化贡献',color=C[1]);ax.set_xticks(xx,qu.quadrant,rotation=10);ax.set(title='重点商品的流量投入与转化产出',ylabel='入围商品中的占比',ylim=(0,.57));ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1));ax.legend();out(fig,'biz_product_allocation')
 fig,ax=plt.subplots(figsize=(10,4.9));top=op.head(8);ax.barh(top.item_id.astype(str)[::-1],top.pv_uv[::-1],color=C[3]);ax.set(title='优先优化的高流量低转化商品',xlabel='浏览用户数',ylabel='商品ID')
 for i,row in enumerate(top.iloc[::-1].itertuples()):ax.text(row.pv_uv+160,i,f'{row.conversion_rate:.2%}',va='center',fontsize=11)
 ax.set_xlim(0,top.pv_uv.max()*1.2);out(fig,'biz_candidate_priority')
 # Exact process diagram for communicating implementation capability.
 fig,ax=plt.subplots(figsize=(11,4));ax.set_xlim(0,11);ax.set_ylim(0,4);ax.axis('off');boxes=[('原始行为日志','100,150,807行'),('分块处理与校验','完整用户历史 · 质量规则'),('分层分析数据','用户 · 商品 · 时段 · Cohort'),('Power BI报表','14张表 · 6页 · 53个视觉对象')]
 for i,(a,b) in enumerate(boxes):
  x=.1+i*2.75;ax.add_patch(FancyBboxPatch((x,1.15),2.45,1.55,boxstyle='round,pad=0.03',facecolor='#EFF4F8',edgecolor='#CBD7E1'));ax.text(x+1.225,2.2,a,ha='center',fontsize=14,weight='bold',color=C[0]);ax.text(x+1.225,1.65,b,ha='center',fontsize=10)
  if i<3:ax.add_patch(FancyArrowPatch((x+2.48,1.9),(x+2.7,1.9),arrowstyle='-|>',mutation_scale=13,color=C[0]))
 ax.text(5.5,.45,'全量计算 → 276项核对 → 可重用指标与运营清单',ha='center',fontsize=14,color=C[0]);out(fig,'biz_data_pipeline')
 # Stream full item summaries to produce stable ranking candidates without loading all SKUs.
 best={50:None,100:None,200:None}
 for t in pd.read_csv(ROOT/'data/processed/item_id_metrics.csv.gz',usecols=['item_id','pv_uv','eligible_pairs','converted_pairs','conversion_rate'],chunksize=500000):
  for minimum in best:
   candidate=t[t.eligible_pairs>=minimum].nlargest(30,'conversion_rate');merged=pd.concat([best[minimum],candidate],ignore_index=True) if best[minimum] is not None else candidate;best[minimum]=merged.nlargest(30,'conversion_rate')
 sets=[set(t.item_id) for t in best.values()];stable=set.intersection(*sets);stable_rows=best[100][best[100].item_id.isin(stable)].sort_values('conversion_rate',ascending=False);stable_rows.to_csv(O/'stable_product_candidates.csv',index=False,encoding='utf-8-sig');stats['stable_top30_all_thresholds']=len(stable);(O/'business_findings.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print(json.dumps(stats,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
