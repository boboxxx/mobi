#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parents[2]/'results/view_intersection_20261004'
d=json.loads((P/'summary_sheng.json').read_bytes());a=json.loads((P/'ambiguity_sheng.json').read_bytes());audit=json.loads((P/'audit_sheng.json').read_bytes())
labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];x=np.arange(6);comparison=next(c for c in d['comparisons'] if c['method']=='union' and c['bitrate']==20000000)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(1,3,figsize=(14,4.6),layout='constrained')
gain=[c['grants']-c['primary_grants'] for c in comparison['classes']];ax[0].bar(x,gain,color='#237b82');ax[0].set_xticks(x,labels,rotation=30,ha='right');ax[0].set(ylabel='Additional grants / 1,920 per class',title='Paid union, 20 Mbps: 3,446 → 3,453',ylim=(0,5))
counts=[c['covered_actual_free_but_model_contact_possible'] for c in a['classes']];ax[1].bar(x,counts,color='#476fa6');ax[1].set_xticks(x,labels,rotation=30,ha='right');ax[1].set(ylabel='Current source-query pairs',title='Actual free; joint model still permits contact')
for i,v in enumerate(counts):ax[1].text(i,v+3,str(v),ha='center',fontsize=9)
gains=[v/1000 for c in audit['pair_checks'] for v in c['horizon_gains_us'] if v>1]
ax[2].hist(gains,bins=[0,1,5,10,25,50,100,200],color='#237b82',edgecolor='white');ax[2].set(xlabel='Geometric horizon gain (ms)',ylabel='Source-query pairs',title='61 of 2,070 have gain > 1 µs')
for z in ax:z.grid(axis='y',alpha=.18);z.set_axisbelow(True)
fig.suptitle('Receiver set intersection under unchanged simultaneous coverage',fontsize=13)
fig.supxlabel('Post-result development; body/motion model and saved causal timings. Collision witnesses are abstract set states, not raw-compatible physical worlds.',fontsize=8)
fig.savefig(P/'view_intersection.png',dpi=180);fig.savefig(P/'view_intersection.pdf',metadata={'CreationDate':None,'ModDate':None})
