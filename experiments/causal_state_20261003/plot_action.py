#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parents[2]/'results/causal_state_20261003';read=lambda n:json.loads((P/n).read_bytes());a=read('action_functional_summary_sheng.json');f=read('functional_summary_sheng.json');t=read('tube_summary_sheng.json');s=read('summary_sheng.json')
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(1,3,figsize=(14,4.6),layout='constrained');names=['State envelope','Snapshot tube','Task correction','Action-eligible'];ds=[s,t,f,a];xx=np.arange(4)
for offset,rate,color in [(-.18,20000000,'#237b82'),(.18,2000000,'#476fa6')]:
 vals=[next(r['grants'] for r in d['comparisons'] if r['method']=='union' and r['bitrate']==rate) for d in ds];ax[0].bar(xx+offset,vals,width=.34,color=color,label=str(rate//1000000)+'Mbps')
 for i,v in enumerate(vals):ax[0].text(i+offset,v+110,str(v),ha='center',fontsize=8)
ax[0].set(ylabel='Grants / 11520 scheduled outcomes',title='Same incomplete XYZ frontend, paid queues');ax[0].set_xticks(xx,names,rotation=20,ha='right');ax[0].legend(fontsize=8);ax[0].set_ylim(0,6000)
labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];x=np.arange(6)
for offset,d,color,label in [(-.18,f,'#476fa6','All task-pair errors'),(.18,a,'#237b82','Action-eligible errors')]:ax[1].bar(x+offset,[r['correction_us']/1000 for r in d['classes']],width=.34,color=color,label=label)
ax[1].set(ylabel='Max95 additive correction (ms)',title='Apply the220ms action filter BEFORE calibration');ax[1].set_xticks(x,labels,rotation=30,ha='right');ax[1].legend(fontsize=8)
methods=['union','lossless_centers','full_xyz'];v=[next(c for c in a['comparisons'] if c['method']==m and c['bitrate']==20000000) for m in methods];xx=np.arange(3)
ax[2].bar(xx-.18,[r['grants'] for r in v],width=.34,color='#237b82',label='Action-eligible policy');ax[2].bar(xx+.18,[r['perfect_grid_oracle_grants'] for r in v],width=.34,color='#b8c5d5',label='Perfect future-grid oracle')
ax[2].set_xticks(xx,['Union','Lossless centers','Full sampled XYZ'],rotation=15,ha='right');ax[2].set(ylabel='Grants / 11520 at20Mbps',title='Strong baseline and diagnostic oracle');ax[2].legend(fontsize=8)
for axis in ax:axis.grid(axis='y',alpha=.18);axis.set_axisbelow(True)
fig.suptitle('Exploratory action-aware expiry: utility improves, one occupied Sprinter grant remains',fontsize=12)
fig.supxlabel('Reused posthoc data; correlated20Hz snapshot outcomes;500ms cap. No untouched validation, continuous physics, ego driving or novelty claim.',fontsize=8)
fig.savefig(P/'action_expiry.png',dpi=180);fig.savefig(P/'action_expiry.pdf',metadata={'CreationDate':None,'ModDate':None})
