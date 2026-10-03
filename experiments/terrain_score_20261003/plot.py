#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/terrain_score_20261003'
rows=json.loads((OUT/'inversion16000/rows.json').read_bytes());low=json.loads((OUT/'inversion/rows.json').read_bytes())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
f,ax=plt.subplots(1,3,figsize=(15,6),gridspec_kw={'width_ratios':[1,1.4,1]})
x=np.arange(3);ax[0].bar(x-.17,[39,32,25],.34,label='Original score',color='#9cabbc');ax[0].bar(x+.17,[10,0,0],.34,label='Terrain-clipped',color='#168272');ax[0].set_xticks(x);ax[0].set_xticklabels(['1/16','1/4','Full']);ax[0].set_ylabel('Surviving known poses / 39');ax[0].set_xlabel('Received budget (nested constraints)');ax[0].set_title('Known counterexamples removed');ax[0].legend(loc='upper right');ax[0].set_ylim(0,45)
for i,r in enumerate(rows):
    ax[1].plot([r['lower_us']/1000,r['upper_us']/1000],[i,i],color='#8797aa',lw=1.5);ax[1].plot(r['lower_us']/1000,i,'o',color='#168272' if r['lower_us'] else '#b34b45',ms=4);ax[1].plot(r['upper_us']/1000,i,'|',color='#8797aa')
ax[1].set_yticks([1.5,5.5,9.5,13.5,17.5,21.5]);ax[1].set_yticklabels(['Audi','Bicycle','Motorcycle','Sprinter','Tesla','Pedestrian']);ax[1].invert_yaxis();ax[1].set_xlabel('Geometric expiry bracket (ms)');ax[1].set_xlim(-15,525);ax[1].set_title('10/24 positive lower bounds\n16,000 nodes; wide upper bounds');ax[1].grid(axis='x',alpha=.2)
for i,rr in enumerate([low,rows]):
    t=[r['elapsed_s'] for r in rr];ax[2].scatter(np.full(len(t),i),t,alpha=.5,color='#168272');ax[2].plot([i-.2,i+.2],[np.median(t)]*2,color='#123941',lw=3)
ax[2].axhline(.5,color='#b34b45',ls='--',label='500 ms study horizon');ax[2].set_xticks([0,1]);ax[2].set_xticklabels(['2,000 nodes','16,000 nodes']);ax[2].set_yscale('log');ax[2].set_ylabel('Measured inversion time (s)');ax[2].set_ylim(.3,20);ax[2].set_title('No timely grants after compute');ax[2].legend(loc='lower right',fontsize=8)
f.suptitle('Terrain-aware score repair: geometric progress, unresolved real-time validity',fontsize=15,y=.99);f.tight_layout(rect=[0,.07,1,.95]);f.text(.5,.025,'Retrospective saved CARLA scans. New thresholds; no fresh risk validation. Body-disc bounds are not mesh collision guarantees.',ha='center',fontsize=9)
f.savefig(OUT/'terrain_repair.png',dpi=180);f.savefig(OUT/'terrain_repair.pdf');plt.close(f)
