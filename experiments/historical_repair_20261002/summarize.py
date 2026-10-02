import json,collections,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/historical_repair_20261002';data=json.loads((OUT/'study/analysis.json').read_bytes());groups=[]
for preset in ['standard','slow','blackout']:
 for method in ['fixed','fine','backfill','backward','backward_fine']:
  runs=[r for r in data['runs'] if r['preset']==preset and r['method']==method];rows=[x for r in runs for x in r['rows']];repairs=[x for r in runs for x in r['repairs']];success=[x for x in repairs if x['decision']['horizon_us']>0];groups.append(dict(preset=preset,method=method,normal_rows=len(rows),geometry=sum(x['horizon_us']>0 for x in rows),timely=sum(x['fresh_admission'] for x in rows),mean_coverage_percent=100*np.mean([x['coverage']['coverage'] for x in runs]),requests=len(repairs),successful_repairs=len(success),timely_repairs=sum(x['receiver_end_us']+200000<x['decision']['endpoint_us'] for x in success),uplink_bytes=sum(r['uplink_bytes'] for r in runs),reply_bytes=sum(x['link']['bytes'] for x in repairs),downlink_bytes=sum(r['downlink_bytes'] for r in runs)))
w=json.loads((OUT/'witness_local.json').read_bytes());s=dict(groups=groups,normal_rows=sum(len(x['rows']) for x in data['runs']),conditions=len(data['runs']),witness_cases=w['cases'],witness_surviving=w['surviving_witnesses'],segment_checks=w['segment_checks'],positive_bound_queries=sum(x['lower_us']>0 and x['upper_us'] is not None for x in w['joint']),max_gap_us=max(x['gap_us'] for x in w['joint']),max_relative_loss_bound=max(x['relative_loss_bound'] for x in w['joint']),data_sha256=hashlib.sha256((OUT/'study/analysis.json').read_bytes()).hexdigest());(OUT/'summary.json').write_text(json.dumps(s,indent=2)+'\n')
labels=['Scalar','Fine','Backfill','Historical','Hist. + fine'];colors=['#64748b','#94a3b8','#b45309','#047857','#6d28d9'];fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
for ax,preset,title in zip(axes,['standard','slow','blackout'],['20 Mbps','0.5 Mbps','Drops at frames 27–29']):
 rows=[x for x in groups if x['preset']==preset];vals=[x['mean_coverage_percent'] for x in rows];bars=ax.bar(np.arange(5),vals,color=colors)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.4,f'{v:.1f}',ha='center',fontsize=9)
 ax.set_xticks(np.arange(5));ax.set_xticklabels(labels,rotation=32,ha='right');ax.set_title(title);ax.set_ylim(0,30);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0].set_ylabel('Actionable time, excluding receiver CPU busy (%)');fig.suptitle('Historical repair: measured sheng services, modeled links',fontsize=13);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(OUT/('paid_coverage.'+ext),dpi=180)
plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4));x=np.arange(18);lo=np.array([r['lower_us']/1000 for r in w['joint']]);hi=np.array([r['upper_us']/1000 for r in w['joint']]);ax.vlines(x,lo,hi,color='#64748b',linewidth=3);ax.scatter(x,lo,color='#047857',label='Verified lower bound');ax.scatter(x,hi,color='#b45309',label='Compatible counterexample upper bound');ax.set_xticks([1,4,7,10,13,16]);ax.set_xticklabels(['c0 ref fixed','c0 ref rate20','c0 reuse fixed','c0 reuse rate20','c2 ref rate20','c2 reuse rate20'],rotation=18,ha='right');ax.set_ylabel('Conditional evidence lifetime (ms)');ax.set_ylim(455,575);ax.set_title('All 18 selected queries have L > 0 after delivered repair');ax.legend(loc='upper right',fontsize=8);ax.grid(axis='y',alpha=.15);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(OUT/('lifetime_bounds.'+ext),dpi=180)
