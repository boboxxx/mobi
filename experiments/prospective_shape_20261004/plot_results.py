#!/usr/bin/env python3
"""Descriptive plots from archived audited results, never used for fitting."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results
 s=json.loads((p/'summary_sheng.json').read_bytes());c=json.loads((p/'comparison_local.json').read_bytes());names=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Pedestrian'];colors=['#777777','#3975b7','#ed8b23','#bb5353','#35866f']
 fig,ax=plt.subplots(1,3,figsize=(16,4.6),layout='constrained')
 methods=['sphere_hull','pose_hull','joint_hull','joint_raw'];labels=['Sphere hull','Pose hull','Joint hull','Full XYZ','Direct deadline'];x=np.arange(4);width=.15
 for i,m in enumerate(methods):ax[0].bar(x+(i-2)*width,[q['primary_grants'][m]/11520*100 for q in c['policies']],width,label=labels[i],color=colors[i])
 ax[0].bar(x+2*width,[q['lease']['minimal']['grants']/11520*100 for q in c['policies']],width,label=labels[4],color=colors[4]);ax[0].set_xticks(x,['20M warm','20M cold','2M warm','2M cold']);ax[0].set_ylabel('Granted scheduled queries (%)');ax[0].set_title('Measured fees + modeled three-FIFO delivery');ax[0].legend(fontsize=7)
 x=np.arange(6)
 for i,m in enumerate(('sphere_hull','pose_hull','joint_hull')):ax[1].bar(x+(i-1)*.25,[q['methods'][m]['oracle_age_gap_us']['p95']/1000 for q in s['classes']],.25,label=labels[i],color=colors[i])
 ax[1].set_xticks(x,names,rotation=25,ha='right');ax[1].set_ylabel('P95 source lifetime gap (ms)');ax[1].set_title('Same body/motion true-center oracle');ax[1].legend(fontsize=7)
 ax[2].bar(x,[100*q['joint_excluded_episodes']/60 for q in s['classes']],color='#3975b7',label='Observed exclusions / 60 planned');ax[2].plot(x,[100*q['single_class_risk_upper95'] for q in s['classes']],'o',color='#ed8b23',label='Single-class one-sided 95% upper');ax[2].plot(x,[100*q['simultaneous_six_class_risk_upper95'] for q in s['classes']],'x',color='#bb5353',label='Six-class simultaneous 95% upper');ax[2].axhline(5,color='#777777',ls=':',label='5% target');ax[2].set_xticks(x,names,rotation=25,ha='right');ax[2].set_ylabel('Episode-any center exclusion risk (%)');ax[2].set_title('Fixed-law qualification; refusals included');ax[2].legend(fontsize=7)
 for v in ax:v.spines[['top','right']].set_visible(False)
 fig.savefig(p/'figure.png',dpi=180);fig.savefig(p/'figure.pdf');plt.close(fig)
if __name__=='__main__':main()
