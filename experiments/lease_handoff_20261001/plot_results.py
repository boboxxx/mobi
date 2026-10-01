#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();v=json.loads((a.results/'validation.json').read_text());g=json.loads((a.results/'replay/age_grid.json').read_text())
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False});fig,ax=plt.subplots(1,3,figsize=(13,3.8));x=np.arange(3);width=.34
    for offset,key,label,color in [(-width/2,'old_gate','Fixed hold/go/brake','#708090'),(width/2,'region_gate','Free-region gate','#007c91')]:
        y=[v['by_speed'][str(s)][key] for s in [0.,.5,1.]];bars=ax[0].bar(x+offset,y,width,label=label,color=color);ax[0].bar_label(bars)
    ax[0].set(xticks=x,xticklabels=['0','0.5','1.0'],xlabel='Hypothetical current speed (m/s)',ylabel='Conditional admissions / 348 cases',ylim=(0,18),title='Same packet and arrival time');ax[0].legend(frameon=False,fontsize=8)
    for key,label,color in [('old_max_ms','Fixed hold/go/brake','#708090'),('region_max_ms','Free-region gate','#007c91')]:
        y=[max(r[key] for r in g if r['speed']==s and r['horizon']==.4) for s in [0.,.5,1.]];ax[1].plot(x,y,'o-',label=label,color=color)
        for i,n in enumerate(y):ax[1].annotate(str(n),(i,n),xytext=(4,5),textcoords='offset points',fontsize=8)
    ax[1].set(xticks=x,xticklabels=['0','0.5','1.0'],xlabel='Hypothetical current speed (m/s)',ylabel='Largest passing age-grid point (ms)',ylim=(0,310),title='Fixed 400 ms evidence expiry')
    for mode,color in [('ackermann','#a15a00'),('relay','#007c91')]:
        r=list(csv.DictReader((a.results/'control/episodes'/('loc0_v1.0_'+mode+'.csv')).open()));t=np.arange(1,len(r)+1)*.05;ax[2].plot(t,[float(i['speed']) for i in r],label=mode,color=color,linewidth=1.3)
    ax[2].axvline(8,color='black',ls='--',lw=1);ax[2].text(8.1,1.15,'brake',fontsize=8);ax[2].axhline(1,color='#bbb',ls=':',lw=1);ax[2].set(xlabel='Actual CARLA time (s)',ylabel='Measured speed (m/s)',title='Continuous controls: separate test');ax[2].legend(frameon=False,fontsize=8,loc='upper left')
    fig.text(.5,.01,'Conditional model results are not physical authorization; all 12 control runs violate the supplied 3 m/s² traction bound.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.06,1,1));fig.savefig(a.results/'comparison.png',dpi=190);fig.savefig(a.results/'comparison.pdf');plt.close(fig)


if __name__=='__main__':main()
