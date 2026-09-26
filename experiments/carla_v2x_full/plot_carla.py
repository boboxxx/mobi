#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
 p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 with (a.analysis/'summary.csv').open() as f:r=list(csv.DictReader(f))
 methods=['no_comm','round_robin','coverage_greedy','singleton_voi','set_independent','set_joint','full_info'];labels=['No comm','Round robin','Coverage','Singleton VoI','Set (indep.)','Set (joint)','Full info'];colors=['#777','#ccb974','#4c72b0','#55a868','#c44e52','#8172b3','#000']
 fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
 for ax,(config,scenario) in zip(axes.flat,[(c,s) for c in ('independent','contention') for s in ('free','hazard_a')]):
  cell={(x['method']):x for x in r if x['config']==config and x['scenario']==scenario};vals=[float(cell[m]['distance_m_mean']) for m in methods];err=[float(cell[m]['distance_m_std']) for m in methods]
  ax.bar(np.arange(len(methods)),vals,yerr=err,color=colors,capsize=3);ax.set_xticks(np.arange(len(methods)),labels,rotation=35,ha='right');ax.set_ylabel('Distance in 5 s (m)');ax.set_title(config+' / '+scenario);ax.grid(axis='y',alpha=.2)
 fig.suptitle('CARLA semantic-LiDAR closed loop: mean ± seed SD (n=5)',fontsize=15);fig.savefig(a.out/'carla_distance.png',dpi=180);fig.savefig(a.out/'carla_distance.pdf');plt.close(fig)


if __name__=='__main__':main()
