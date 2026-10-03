#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ap=argparse.ArgumentParser()
ap.add_argument('--summary',required=True,type=Path)
ap.add_argument('--out',required=True,type=Path)
a=ap.parse_args()
s=json.loads(a.summary.read_text())
fig,axes=plt.subplots(1,3,figsize=(14,4.8))
ax=axes[0]
values=[s['fixed_direct_baseline']['positive_remaining']]+[g['positive_remaining'] for g in s['fixed_groups']]
bars=ax.bar(range(4),values,color=['#34495e','#adb5bd','#2878b5','#d56b42'])
ax.bar_label(bars,padding=3)
ax.set_xticks(range(4),['Direct','Repair 0','Repair 256','Repair 4096'],rotation=20)
ax.set_ylim(0,10);ax.set_ylabel('Tasks with positive modeled remainder / 36')
ax.set_title('(a) Fixed budgets: all costs charged')
ax=axes[1]
rs=[r for r in s['adaptive_tasks'] if r['positive_trials']>0 or r['direct_positive_trials']>0]
x=np.arange(len(rs));w=.36
for shift,key,color,label in [(-w/2,'direct','#34495e','Direct, min of 3'),(w/2,'','#2878b5','Adaptive, min of 3')]:
    prefix='direct_' if key else ''
    ax.bar(x+shift,[r['min_'+prefix+'remaining_us']/1000 for r in rs],w,color=color,label=label)
labels=[('Bike' if 'century' in r['blueprint'] else 'Moto')+' '+str(r['query_index'])+'\n'+str(r['radius_um']//1000)+'mm' for r in rs]
ax.set_xticks(x,labels,fontsize=8);ax.set_ylabel('Minimum modeled remainder (ms)')
ax.set_title('(b) Same-trial direct baseline');ax.legend(fontsize=8)
ax.set_ylim(0,105)
ax.text(.02,.80,'Other 29 tasks: 0 in every trial',transform=ax.transAxes,va='top',fontsize=8)
ax=axes[2]
for budget,color,marker in [(0,'#adb5bd','o'),(256,'#2878b5','x'),(4096,'#d56b42','+')]:
    rr=[r for r in s['fixed_rows'] if r['budget']==budget]
    ax.scatter([r['lower_us']/1000 for r in rr],[r['upper_us']/1000 for r in rr],s=30,c=color,marker=marker,label=str(budget)+' visits',alpha=.8)
ax.plot([0,500],[0,500],'--',color='#666666',linewidth=1)
ax.set_xlim(-10,510);ax.set_ylim(-10,530);ax.set_xlabel('Certified lower horizon L (ms)')
ax.set_ylabel('Model upper horizon U (ms)');ax.set_title('(c) Tightness remains unresolved');ax.legend(fontsize=8,loc='lower right')
fig.suptitle('Finite sheng replay: repair can buy margin, but not yet tight expiry',fontsize=14,y=.97)
fig.subplots_adjust(left=.065,right=.99,bottom=.2,top=.83,wspace=.36)
a.out.mkdir(exist_ok=True,parents=True)
fig.savefig(a.out/'comparison.png',dpi=180)
fig.savefig(a.out/'comparison.pdf')
