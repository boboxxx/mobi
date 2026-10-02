#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    frontier=json.loads((a.results/'frontier/analysis.json').read_text());actuator=json.loads((a.results/'actuator/analysis.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(11,4.3));colors=['#526579','#009b82'];x=np.arange(2);width=.34
    for method,color,offset in [('full',colors[0],-width/2),('shell',colors[1],width/2)]:
        medians=[]
        for kind in ['all_observed_rays','transmitted_subset']:
            rows=[r for r in frontier['rows'] if r['kind']==kind and not r['cold_ordered_index']]
            medians.append(float(np.median([r[method+'_ms'] for r in rows])))
        bars=axes[0].bar(x+offset,medians,width,color=color,label='Full domain' if method=='full' else 'Ordered shells')
        for bar,value in zip(bars,medians):axes[0].text(bar.get_x()+bar.get_width()/2,value+15,f'{value:.1f}',ha='center',fontsize=9)
    axes[0].set_xticks(x,['All observed rays\n28 archived inputs','Sent subset\n9 archived inputs']);axes[0].set_ylabel('Projection + frontier cost (ms)');axes[0].set_ylim(0,1000);axes[0].legend(frameon=False);axes[0].set_title('Equivalent joint horizons; warm ordered index')
    for mode,color,label in [('automatic',colors[0],'Automatic'),('manual1',colors[1],'Manual first gear')]:
        groups=sorted([g for g in actuator['groups'] if g['mode']==mode],key=lambda g:g['go_ticks'])
        axes[1].plot([g['go_ticks']*50 for g in groups],[g['median_progress_m']*1000 for g in groups],marker='o',color=color,label=label)
    axes[1].set_xlabel('Throttle phase duration (ms)');axes[1].set_ylabel('Median displacement after braking (mm)');axes[1].set_xticks([50,100,200,400]);axes[1].axhline(0,color='#b0b0b0',lw=.7);axes[1].legend(frameon=False);axes[1].set_title('Separate actuator probes: 4 repeats per point')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    fig.text(.5,.015,'Synchronous CARLA diagnostics. Timings are not WCET; actuator probes do not establish evidence-guided driving.',ha='center',fontsize=8,color='#4a4a4a')
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(str(a.out)+'.png',dpi=180);fig.savefig(str(a.out)+'.pdf');plt.close(fig)


if __name__=='__main__':main()
