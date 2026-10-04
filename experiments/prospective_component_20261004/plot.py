#!/usr/bin/env python3
"""Scientific figures from predefined summary; capture/source and service denominators explicit."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/prospective_component_20261004'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--summary',type=Path,default=P/'summary_sheng.json');a=ap.parse_args();d=json.loads(a.summary.read_bytes());classes=list(d['registry']);names=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];lookup={(r['blueprint'],r['family']):r for r in d['source']};palette=['#777777','#3B75AF','#D78A32','#379263'];x=np.arange(6)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(12,4.4),sharey=True)
    for ax,mode in zip(axes,('mean','modes')):
        methods=['joint','ridge','local_'+mode,'component_'+mode]
        for i,(method,color) in enumerate(zip(methods,palette)):
            ax.bar(x+(i-1.5)*.19,[lookup[b,method]['p95_oracle_gap_us']/1000 for b in classes],.18,color=color,label=method)
        ax.set_xticks(x,names,rotation=25);ax.set_title('Single center' if mode=='mean' else 'Multiple centers');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes[0].set_ylabel('P95 oracle − authorized source age (ms)');axes[1].legend(fontsize=9);fig.suptitle('Independent test: source conservativeness on captured scans (lower is better)');fig.tight_layout();fig.savefig(P/'source_gap.png',dpi=180);fig.savefig(P/'source_gap.pdf');plt.close(fig)
    cells=[c for c in d['service'] if c['rate']==20000000 and c['startup']=='cold'];fig,axes=plt.subplots(1,2,figsize=(13,5));x=np.arange(len(cells));labels=[c['method'].replace('_function','\nfunction').replace('_deadline','\ndeadline') for c in cells]
    axes[0].bar(x,[100*c['raw_grants']/c['scheduled_queries'] for c in cells],color='#95ABC2',label='Raw measured policy');axes[0].bar(x,[100*c['deployable_grants']/c['scheduled_queries'] for c in cells],width=.48,color='#379263',label='Certificate accepted');axes[0].set_ylabel('Granted queries / all planned queries (%)');axes[0].legend(fontsize=8);axes[0].set_title('20 Mbit/s, paid cold initialization')
    axes[1].plot(x,[100*c['conditional_center_upper'] for c in cells],'o',color='#D78A32',label='Source-score exclusion upper bound');axes[1].plot(x,[100*c['conditional_age_upper'] for c in cells],'x',color='#3B75AF',label='Source-age/action failure upper bound');axes[1].axhline(5,color='black',ls='--',lw=1,label='5% target');axes[1].set_ylabel('Simultaneous conditional risk upper bound (%)');axes[1].set_title('Independent selected-query certification');axes[1].legend(fontsize=8)
    for ax in axes:ax.set_xticks(x,labels,rotation=65,ha='right',fontsize=7);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.tight_layout();fig.savefig(P/'certified_service.png',dpi=180);fig.savefig(P/'certified_service.pdf');plt.close(fig)
    print('PREDEFINED_SCIENTIFIC_FIGURES_COMPLETE')
if __name__=='__main__':main()
