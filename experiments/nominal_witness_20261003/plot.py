#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--summary',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();s=json.loads(a.summary.read_bytes());r=s['rows'];fig,axes=plt.subplots(1,2,figsize=(12,5.6));ax=axes[0]
for bp,label,color in [('vehicle.audi.a2','Audi','#386cb0'),('vehicle.diamondback.century','Bicycle','#1b9e77'),('vehicle.kawasaki.ninja','Motorcycle','#e6ab02'),('vehicle.mercedes.sprinter','Sprinter','#d95f02'),('vehicle.tesla.model3','Tesla','#e7298a'),('walker.pedestrian.0001','Pedestrian','#7570b3')]:
 rows=[x for x in r if x['blueprint']==bp]
 ax.scatter([x['lower_us']/1000 for x in rows],[x['nominal_pool_upper_us']/1000 for x in rows],s=35,label=label,c=color,alpha=.8)
ax.plot([0,500],[0,500],'--',color='#777777',lw=1);ax.axhline(240,color='#b2182b',ls=':',lw=1.3);ax.text(12,246,'240ms fixed reserve',fontsize=9,color='#b2182b');ax.set_xlim(-10,510);ax.set_ylim(0,510);ax.set_xlabel('Existing 4096-visit lower bound L (ms)');ax.set_ylabel('Receiver-message upper witness U (ms)');ax.set_title('(a) All 36 upper bounds tighten; gaps remain');ax.legend(fontsize=8,loc='upper left',ncol=2)
ax=axes[1];x=np.arange(len(r));ax.axhspan(0,240,color='#fee8e6',zorder=0);ax.scatter(x,[t['nominal_pool_upper_us']/1000 for t in r],s=28,marker='o',color='#2878b5',label='Nominal message witness');ax.scatter(x,[t['actual_pool_upper_us']/1000 for t in r],s=30,marker='x',color='#d56b42',label='Actual raw witness / prior cap');ax.axhline(240,color='#b2182b',ls=':',lw=1.3)
for b in [5.5,11.5,17.5,23.5,29.5]:ax.axvline(b,color='#cccccc',lw=.7)
ax.set_xticks([2.5,8.5,14.5,20.5,26.5,32.5],['Audi','Bicycle','Moto','Sprinter','Tesla','Walker']);ax.set_ylim(0,530);ax.set_ylabel('Upper bound (ms)');ax.set_xlabel('Each class: query 0/1 at 0, 5 and 50mm radii');ax.set_title('(b) Seven raw-data tasks cannot cover reserve');ax.legend(fontsize=8,loc='upper right');ax.text(.02,.10,'Shaded: impossible under the frozen model\nwith the declared 240ms reserve',transform=ax.transAxes,fontsize=9,color='#8b1919')
fig.suptitle('Feasible-state witnesses separate model limitations from missing computation',fontsize=13,y=.97);fig.subplots_adjust(left=.075,right=.99,bottom=.15,top=.86,wspace=.27);a.out.mkdir(parents=True,exist_ok=True);fig.savefig(a.out/'comparison.png',dpi=180);fig.savefig(a.out/'comparison.pdf')
