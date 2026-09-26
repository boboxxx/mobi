#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
 p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 with (a.analysis/'summary.csv').open() as f:rows=list(csv.DictReader(f))
 methods=['no_comm','round_robin','coverage_greedy','singleton_voi','set_independent','set_joint','full_info']
 labels=['No comm','Round robin','Coverage','Singleton VoI','Set (indep.)','Set (joint)','Full info']
 colors=['#777777','#ccb974','#4c72b0','#55a868','#c44e52','#8172b3','#000000']
 scenarios=['free','hazard_a','hazard_b','both_hazard'];configs=['ideal','independent','contention','burst','short_deadline','one_slot']
 fig,axes=plt.subplots(2,3,figsize=(15,8),sharey=True,layout='constrained')
 for ax,config in zip(axes.flat,configs):
  vals=[]
  for method in methods:
   cell=[float(r['progress_mean']) for r in rows if r['config']==config and r['method']==method and r['scenario'] in scenarios]
   vals.append(np.mean(cell))
  ax.bar(np.arange(len(methods)),vals,color=colors);ax.set_title(config);ax.set_xticks(np.arange(len(methods)),labels,rotation=35,ha='right');ax.set_ylim(0,1.02);ax.grid(axis='y',alpha=.2)
 axes[0,0].set_ylabel('Mean post-clear progress opportunity');axes[1,0].set_ylabel('Mean post-clear progress opportunity')
 fig.suptitle('Finite mechanism sweep: 1,000 paired seeds per cell',fontsize=15);fig.savefig(a.out/'mechanism_progress.png',dpi=180);fig.savefig(a.out/'mechanism_progress.pdf');plt.close(fig)
 with (a.analysis/'overall_comparisons.csv').open() as f:comp=list(csv.DictReader(f))
 target=[r for r in comp if r['method']=='set_joint' and r['baseline']=='set_independent']
 target.sort(key=lambda r:configs.index(r['config']))
 means=np.array([float(r['mean_progress_diff']) for r in target]);lo=np.array([float(r['ci_low']) for r in target]);hi=np.array([float(r['ci_high']) for r in target])
 fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained');x=np.arange(len(target));ax.errorbar(x,means,yerr=[means-lo,hi-means],fmt='o',capsize=4,color='#8172b3');ax.axhline(0,color='black',lw=1);ax.set_xticks(x,[r['config'] for r in target],rotation=20);ax.set_ylabel('Progress difference: joint − independent set');ax.set_title('Effect of modeling joint message arrival (95% paired bootstrap CI)');ax.grid(axis='y',alpha=.2);fig.savefig(a.out/'joint_arrival_effect.png',dpi=180);fig.savefig(a.out/'joint_arrival_effect.pdf');plt.close(fig)


if __name__=='__main__':main()
