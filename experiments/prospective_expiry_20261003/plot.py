#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parents[2]/'results/prospective_expiry_20261003'
d=json.loads((P/'action_functional_summary_sheng.json').read_bytes());base=json.loads((P/'summary_sheng.json').read_bytes());labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];x=np.arange(6)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
v=[r['deadline_overstatement_episodes']/60*100 for r in d['classes']];up=[r['one_sided_95_risk_upper']*100 for r in d['classes']];ax[0].bar(x,v,color='#476fa6');ax[0].errorbar(x,v,yerr=[np.zeros(6),np.array(up)-v],fmt='none',color='#444',capsize=3);ax[0].axhline(5,ls='--',lw=1,color='#444');ax[0].set(ylabel='Episode-any overstatement (%)',title='Fresh60tests/class: one-sided95%bounds');ax[0].set_xticks(x,labels,rotation=30,ha='right')
methods=['union','lossless_centers','full_xyz'];xx=np.arange(3)
for offset,rate,color in [(-.18,20000000,'#237b82'),(.18,2000000,'#476fa6')]:
 values=[next(c['grants'] for c in d['comparisons'] if c['bitrate']==rate and c['method']==m) for m in methods];ax[1].bar(xx+offset,values,width=.34,color=color,label=str(rate//1000000)+'Mbps')
 for i,v in enumerate(values):ax[1].text(i+offset,v+100,str(v),ha='center',fontsize=8)
ax[1].set_xticks(xx,['Union','Lossless centers','Full sampled XYZ'],rotation=15,ha='right');ax[1].set(ylabel='Grants /11520scheduled outcomes',title='Action-eligible policy, paid CPU/link queues');ax[1].legend(fontsize=8);ax[1].margins(y=.15)
ax[2].bar(x,[r['correction_us']/1000 for r in d['classes']],color='#237b82');ax[2].set_xticks(x,labels,rotation=30,ha='right');ax[2].set(ylabel='Calibrated additive correction(ms)',title='Max95freshcalibration, fixed220msfilter')
for a in ax:a.grid(axis='y',alpha=.18);a.set_axisbelow(True)
fig.suptitle('Prospectively frozen action-eligible source-aged expiry',fontsize=13)
fig.supxlabel('Known-class finite20Hzfuture occupancy grid,500mscap; risk conditional on iid law. No actual wireless, ego driving or continuous physics claim.',fontsize=8)
fig.savefig(P/'prospective_expiry.png',dpi=180);fig.savefig(P/'prospective_expiry.pdf',metadata={'CreationDate':None,'ModDate':None})
