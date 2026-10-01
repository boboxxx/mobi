#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();rows=list(csv.DictReader((a.results/'analysis/test_predictions.csv').open()));report=json.loads((a.results/'analysis/report.json').read_text())
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False});fig,ax=plt.subplots(1,3,figsize=(13,3.8));colors={'constant':'#708090','state':'#007c91'}
    for kind in ['constant','state']:
        r=[x for x in rows if x['kind']==kind];finite=[x for x in r if x['predicted_stop_s']];color=colors[kind]
        if finite:ax[0].scatter([float(x['observed_stop_s']) for x in finite if x['observed_stop_s']],[float(x['predicted_stop_s']) for x in finite if x['observed_stop_s']],s=15,alpha=.4,label=kind,color=color)
        speeds=[float(x['speed']) for x in finite];order=np.argsort(speeds)
        if finite:ax[1].plot(np.array(speeds)[order],np.array([float(x['predicted_stop_s']) for x in finite])[order],'.',label=kind,color=color,markersize=3)
    limits=ax[0].get_xlim();upper=max(limits[1],ax[0].get_ylim()[1]);ax[0].plot([0,upper],[0,upper],ls='--',lw=1,color='black');ax[0].set(xlabel='Observed persistent speed-band time (s)',ylabel='Calibrated upper bound (s)',title='400 held-out episodes');ax[0].legend(frameon=False)
    ax[1].axhline(.27,ls=':',lw=1,color='black',label='400 ms expiry − 130 ms age');ax[1].set(xlabel='Measured current speed (m/s)',ylabel='Calibrated upper bound (s)',title='Current-state dependence');ax[1].legend(frameon=False,fontsize=8)
    x=np.arange(2);width=.35
    for offset,key,label,color in [(-width/2,'counterfactual_admissions','Counterfactual admissions','#007c91'),(width/2,'joint_exceedances','Joint bound exceedances','#bd5038')]:
        bars=ax[2].bar(x+offset,[report['methods'][k][key] for k in ['constant','state']],width,label=label,color=color);ax[2].bar_label(bars)
    ax[2].set(xticks=x,xticklabels=['Constant','State'],ylabel='Episodes / 400',ylim=(0,450),title='Same region, age and risk target');ax[2].legend(frameon=False,fontsize=8)
    fig.text(.5,.01,'Sampled finite-window calibration under a fixed episode law; no continuous-time, adaptive-policy, or physical authorization claim.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.06,1,1));fig.savefig(a.results/'comparison.png',dpi=190);fig.savefig(a.results/'comparison.pdf');plt.close(fig)


if __name__=='__main__':main()
