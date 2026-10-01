#!/usr/bin/env python3
"""Recompute paired comparisons and figures from the downloaded sheng CSVs."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('results',type=Path);args=parser.parse_args();root=args.results
    mainrows=read(root/'main38500/per_episode.csv');extra=read(root/'stationary5500/per_episode.csv')
    lookup={(r['config'],r['method'],int(r['seed'])):r for r in mainrows+extra}
    configs=list(dict.fromkeys(r['config'] for r in mainrows));rng=np.random.default_rng(20261003);out=[]
    seeds=sorted({int(r['seed']) for r in mainrows});n=len(seeds)
    for config in configs:
        for baseline in ['group_refresh','deterministic_mpc3','stationary_discounted']:
            for metric in ['valid_fraction','false_valid_fraction']:
                x=np.array([float(lookup[config,'stochastic_mpc3',s][metric])-float(lookup[config,baseline,s][metric]) for s in seeds])
                boot=x[rng.integers(0,n,(4000,n))].mean(1)
                out.append(dict(config=config,baseline=baseline,metric=metric,diff=x.mean(),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975)))
    with (root/'combined_comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n');w.writeheader();w.writerows(out)
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.5),constrained_layout=True)
    selected=['uniform','heterogeneous','three_regions','switch_required']
    ax=axes[0]
    for j,(baseline,color,label) in enumerate([('group_refresh','#b17a3a','Group refresh'),
             ('deterministic_mpc3','#447e92','Deterministic MPC3'),('stationary_discounted','#704e94','Stationary reference')]):
        rows=[next(r for r in out if r['config']==c and r['baseline']==baseline and r['metric']=='valid_fraction') for c in selected]
        y=np.array([r['diff']*100 for r in rows]);lo=np.array([r['ci_low']*100 for r in rows]);hi=np.array([r['ci_high']*100 for r in rows])
        ax.errorbar(np.arange(4)+(j-1)*.16,y,yerr=[y-lo,hi-y],fmt='o',capsize=3,label=label,color=color)
    ax.set_xticks(range(4),['Uniform','Heterogeneous','Three regions','Switching'])
    ax.set_ylabel('Candidate − baseline valid opportunities (pp)')
    ax.set_title('Strong baselines remove the core advantage');ax.legend(frameon=False,fontsize=8)
    ax.axhline(0,color='gray',ls='--',lw=.8)
    ax=axes[1];methods=['edf','group_refresh','stochastic_mpc3','stationary_discounted']
    values=[np.mean([float(lookup['ttl_overestimate_one',m,s]['false_valid_fraction']) for s in seeds])*100 for m in methods]
    ax.bar(range(4),values,color=['#999999','#b17a3a','#447e92','#704e94'])
    ax.set_xticks(range(4),['EDF','Group','Candidate','Stationary'])
    ax.set_ylabel('False-valid decision epochs (%)');ax.set_ylim(0,65)
    ax.set_title('Overestimating validity by one slot is harmful')
    for i,v in enumerate(values):ax.text(i,v+1,f'{v:.1f}%',ha='center')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    fig.suptitle('44,000 synthetic episodes executed on sheng • 500 paired seeds per comparison\nKnown free evidence and supplied validity bounds; these are not driving safety rates',fontsize=11)
    fig.savefig(root/'findings.png',dpi=180);fig.savefig(root/'findings.pdf')


if __name__=='__main__':main()
