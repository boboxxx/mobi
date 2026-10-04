#!/usr/bin/env python3
"""Publication-style descriptive figure, entirely from accepted archived outputs."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'summary_sheng.json').read_bytes());x=json.loads((p/'diagnostic_sheng.json').read_bytes());fig,ax=plt.subplots(1,2,figsize=(10,3.5),layout='constrained');labels=['20M warm','20M cold','2M warm','2M cold'];xx=np.arange(4)
 for i,(method,label) in enumerate([('sphere_hull','Sphere / hull'),('pose_hull','Pose / hull'),('joint_hull','Joint / hull')]):ax[0].bar(xx+(i-1.5)*.2,[v['grants'][method] for v in d['policies']],width=.2,label=label)
 ax[0].bar(xx+1.5*.2,[v['optimized_raw_grants'] for v in x['policies']],width=.2,label='Joint / optimized RAW');ax[0].set_xticks(xx,labels);ax[0].set_ylabel('Grants per 11,520 planned queries');ax[0].legend(fontsize=7);ax[0].set_title('Measured paid replay (development)')
 names=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];xx=np.arange(6);ax[1].bar(xx-.18,[v['methods']['sphere_hull']['oracle_age_gap_us']['p95']/1000 for v in d['classes']],width=.36,label='Sphere');ax[1].bar(xx+.18,[v['joint_oracle_gap_p95_ms'] for v in x['classes']],width=.36,label='Joint');ax[1].set_xticks(xx,names,rotation=25,ha='right');ax[1].set_ylabel('P95 source age gap to center oracle (ms)');ax[1].legend(fontsize=8);ax[1].set_title('Solver precision does not remove model gaps')
 fig.suptitle('Reused CARLA data; 72 source tilt-prior violations; no fresh risk qualification',fontsize=10);fig.savefig(p/'figure.png',dpi=180);fig.savefig(p/'figure.pdf');plt.close(fig)
if __name__=='__main__':main()
