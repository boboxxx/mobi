#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();root=a.results
    r=json.loads((root/'validation.json').read_text());e=json.loads((root/'execution_analysis.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    pairs=[('ablation','reference','combined'),('binary','json_combined','binary_combined'),('proposal','binary_receiver_full','binary_receiver_hints')]
    left=[r[g][p]['median_on_geometry_positive']['age_s']*1000 for g,p,q in pairs];right=[r[g][q]['median_on_geometry_positive']['age_s']*1000 for g,p,q in pairs];x=np.arange(3)
    axes[0].bar(x-.18,left,.36,label='Paired reference');axes[0].bar(x+.18,right,.36,label='Paired optimized')
    axes[0].axhline(120,color='crimson',ls='--',label='Fixed hold budget');axes[0].set_xticks(x,['JSON lookup + hints','Lossless binary wire','Receiver-only proposals'])
    axes[0].set_ylabel('Median evidence age on 87 positives (ms)');axes[0].legend(fontsize=8);axes[0].set_title('Separate paired runs; historical acquisition + modeled link')
    for offset,hold,color in [(-.14,.05,'tab:blue'),(.14,.1,'tab:orange')]:
        for i,target in enumerate([0.,.5,1.]):
            values=[p['incremental_forward_m']*100 for p in e['paired'] if p['target']==target and p['hold']==hold]
            axes[1].scatter(np.full(3,i+offset),values,color=color,label='%d ms hold'%(hold*1000) if i==0 else None)
    axes[1].axhline(0,color='gray',lw=.8);axes[1].set_xticks(np.arange(3),['0','0.5','1.0']);axes[1].set_xlabel('Target preparation speed (m/s); actual speed logged')
    axes[1].set_ylabel('Extra forward motion over brake-only (cm)');axes[1].set_title('Actual CARLA: 18 matched pairs, 3 spawn locations');axes[1].legend()
    fig.suptitle('Faster conditional verification does not make a stalled policy useful',fontsize=13)
    fig.savefig(root/'comparison.png',dpi=170);plt.close(fig)


if __name__=='__main__':main()
