#!/usr/bin/env python3
"""Plot full scheduled denominators, risk and strong same-state baselines."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parents[2]/'results/causal_state_20261003'
primary=json.loads((P/'summary_sheng.json').read_bytes());tube=json.loads((P/'tube_summary_sheng.json').read_bytes());labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];x=np.arange(6)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
for offset,d,field,color,label in [(-.18,primary,'false_exclusion_episodes','#476fa6','Current-center family'),(.18,tube,'future_excluded_episodes','#237b82','Future-snapshot tube')]:
    values=np.array([r[field]/60*100 for r in d['classes']]);upper=np.array([r['one_sided_95_risk_upper']*100 for r in d['classes']]);ax[0].bar(x+offset,values,width=.34,color=color,label=label);ax[0].errorbar(x+offset,values,yerr=[np.zeros(6),upper-values],fmt='none',color=color,capsize=3)
ax[0].axhline(5,ls='--',color='#444',lw=1);ax[0].set(ylabel='Episode-any exclusion (%)',title='Observed risks and one-sided 95% bounds');ax[0].set_xticks(x,labels,rotation=30,ha='right');ax[0].legend(fontsize=8)
methods=['union','lossless_centers','full_xyz'];names=['Union','Lossless centers','Full sampled XYZ'];xx=np.arange(3)
for offset,rate,color in [(-.18,20000000,'#237b82'),(.18,2000000,'#476fa6')]:
    v=[next(c['grants'] for c in tube['comparisons'] if c['bitrate']==rate and c['method']==m) for m in methods];ax[1].bar(xx+offset,v,width=.34,color=color,label=str(rate//1000000)+'Mbps')
    for i,n in enumerate(v):ax[1].text(i+offset,n+max(v+[1])*.025,str(n),ha='center',fontsize=8)
ax[1].set(ylabel='Grants / 11520 scheduled query outcomes',title='Tube utility after causal queue costs');ax[1].set_xticks(xx,names,rotation=15,ha='right');ax[1].legend(fontsize=8);ax[1].margins(y=.15)
for offset,d,color,label in [(-.18,primary,'#476fa6','Current-center family'),(.18,tube,'#237b82','Future-snapshot tube')]:
    ax[2].bar(x+offset,[r['radius_um']/1e6 for r in d['classes']],width=.34,color=color,label=label)
ax[2].set(ylabel='Calibrated radius (m)',title='Max95 risk calibration cost');ax[2].set_xticks(x,labels,rotation=30,ha='right');ax[2].legend(fontsize=8)
for a in ax:a.grid(axis='y',alpha=.18);a.set_axisbelow(True)
fig.suptitle('Fresh moving-actor study: source-aged evidence and finite prediction tubes',fontsize=13)
fig.supxlabel('Finite known-class snapshot family; conditional iid risk statement. Shared CPU/link queues; modeled clocks/links, no live ego driving.',fontsize=9)
fig.savefig(P/'causal_state.png',dpi=180);fig.savefig(P/'causal_state.pdf',metadata={'CreationDate':None,'ModDate':None})
