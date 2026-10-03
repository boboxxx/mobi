#!/usr/bin/env python3
"""Render descriptive class-level results; queries are not independent samples."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parents[2]/'results/positive_state_20261003'
d=json.loads((P/'summary_sheng.json').read_bytes()); c=d['classes']; x=np.arange(6)
labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axes=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
obs=np.array([r['false_exclusion_episodes']/60*100 for r in c]);up=np.array([r['unconditional_one_sided_95_upper']*100 for r in c])
axes[0].bar(x,obs,color='#b34838',width=.6)
axes[0].errorbar(x,obs,yerr=[np.zeros(6),up-obs],fmt='none',color='#343434',capsize=4,label='One-sided 95% upper bound')
axes[0].axhline(5,color='#555555',ls='--',lw=1,label='Nominal marginal error 5%')
axes[0].set(ylabel='Any-view center exclusion (%)',ylim=(0,20),title='Coverage: 60 scheduled tests / class')
axes[0].legend(fontsize=8,loc='upper left')
for i,r in enumerate(c):axes[0].text(i,obs[i]+.25,str(r['false_exclusion_episodes'])+'/60',ha='center',fontsize=8)
positive=[r['positive_modeled_query_results'] for r in c]; refused=[r['refused']*4 for r in c]
axes[1].bar(x,positive,color='#237b82',label='Positive modeled remainder')
axes[1].bar(x,refused,bottom=positive,color='#b9bec6',label='Queries in refused episodes')
axes[1].set(ylim=(0,255),ylabel='Query outcomes / 240 scheduled',title='Utility after charged modeled costs')
axes[1].axhline(240,color='#555555',ls=':',lw=1)
axes[1].legend(fontsize=8,loc='upper left')
for i,n in enumerate(positive):axes[1].text(i,n-13,str(n),ha='center',color='white',fontsize=9)
axes[2].bar(x,[r['radius_um']/1e6 for r in c],color='#476fa6')
axes[2].set(ylabel='Calibrated center radius (m)',title='All XYZ proposals retained',ylim=(0,1.5))
for i,r in enumerate(c):axes[2].text(i,r['radius_um']/1e6+.035,f"{r['radius_um']/1e6:.3f}",ha='center',fontsize=9)
for ax in axes:ax.set_xticks(x,labels,rotation=30,ha='right');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('Fresh CARLA static study: calibrated center unions and conditional expiry',fontsize=14)
fig.supxlabel('705 / 1440 positive queries; 17 / 360 excluded episodes. Correlated queries; offline two-view availability. No physical safety claim.',fontsize=9)
fig.savefig(P/'positive_state.png',dpi=180)
fig.savefig(P/'positive_state.pdf',metadata={'CreationDate':None,'ModDate':None})
