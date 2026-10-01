#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):return list(csv.DictReader(path.open()))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();root=a.results
    geometry=read(root/'geometry/geometry.csv');renewal=[r for r in read(root/'renewal/renewal.csv') if r['geometry']=='True']
    fig,axes=plt.subplots(1,3,figsize=(15,4.7),layout='constrained')
    labels=[];old=[];new=[]
    for scene in ['far','free']:
        for speed in [0.,.5,1.]:
            rows=[r for r in geometry if r['cloud']=='dense_0_'+scene+'_00' and float(r['speed'])==speed]
            labels.append('%s\nv=%g'%(scene,speed))
            old.append(max([float(r['horizon']) for r in rows if r['arbitrary_geometry']=='True'] or [0])*1000)
            new.append(max([float(r['horizon']) for r in rows if r['policy_geometry']=='True'] or [0])*1000)
    x=np.arange(6);axes[0].bar(x-.18,old,.36,label='Arbitrary acceleration');axes[0].bar(x+.18,new,.36,label='Restricted policy')
    axes[0].set_xticks(x,labels);axes[0].set_ylabel('Largest passing grid horizon (ms)');axes[0].set_ylim(0,460);axes[0].legend(fontsize=8)
    axes[0].set_title('Conditional geometry: 6 / 36 have evidence\n30 other configurations remain rejected',fontsize=10)
    values=[np.array([float(r[k])*1000 for r in renewal]) for k in ['full_age_s','age_s']]
    axes[1].boxplot(values,labels=['Full projection','Selected-ray bounds'],showfliers=True)
    axes[1].axhline(120,color='crimson',ls='--',label='Fixed hold budget')
    axes[1].set_ylabel('Age incl. acquisition + modeled link (ms)');axes[1].legend(fontsize=8)
    axes[1].set_title('87 geometry positives; zero timely stop gates\nPaired saved-scan computation, not driving',fontsize=10)
    rows=[r for r in read(root/'sensitivity/episodes/tesla_10_v2.0.csv') if r['phase']=='brake']
    speed0=float(rows[0]['before_speed']);t=np.arange(len(rows)+1)*.05;v=np.r_[speed0,[float(r['speed']) for r in rows]]
    bound=.02+(speed0+3*.02)/4
    axes[2].plot(t,v,marker='.',label='Recorded speed');axes[2].axvline(bound,color='crimson',ls='--',label='Stop time from assumed bounds')
    axes[2].axhline(.02,color='gray',ls=':',label='Stop band (0.02 m/s)');axes[2].set_xlim(0,1.)
    axes[2].set_xlabel('Time after brake command (s)');axes[2].set_ylabel('Own-vehicle speed (m/s)');axes[2].legend(fontsize=8)
    axes[2].set_title('Actual CARLA actuator counterexample\nTesla, throttle 1.0 → brake 0.5',fontsize=10)
    fig.suptitle('Policy-conditioned validity: narrower geometry does not establish executable safety',fontsize=13)
    fig.savefig(root/'comparison.png',dpi=170);plt.close(fig)


if __name__=='__main__':main()
