#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results;s=json.loads((r/'study/analysis.json').read_bytes())
    groups=[[x for x in s['rows'] if x['method']==m] for m in ['fixed_K','coarse_set','fine_set']];labels=['Fixed-K','Coarse position','Fine position'];colors=['#566573','#2874a6','#1e8449']
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained');counts=[len({(x['run'],x['id']) for x in g if x['geometry']}) for g in groups]
    bars=axes[0].bar(np.arange(3),counts,color=colors);axes[0].bar_label(bars,labels=[str(n)+'/12' for n in counts]);axes[0].set_ylim(0,13);axes[0].set_ylabel('Targets with conditional geometry');axes[0].set_title('Same physical/raw observation contract')
    for i,(g,c) in enumerate(zip(groups,colors)):
        axes[1].scatter(np.full(len(g),i),[x['total_ms'] for x in g],s=20,alpha=.5,color=c)
        axes[1].scatter(i,np.median([x['total_ms'] for x in g]),marker='_',s=300,color='black',linewidths=2)
    axes[1].axhline(250,color='#c0392b',ls='--',lw=1.2,label='Latest passing 50 ms age tick');axes[1].set_ylabel('All charged costs before tick rounding (ms)');axes[1].set_title('Timely calls: 9/36, 9/36, 1/36');axes[1].legend(fontsize=8)
    for ax in axes:ax.set_xticks(np.arange(3),labels);ax.tick_params(axis='x',labelsize=9);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('sheng: common exact transport/cache and conservative local computation',fontsize=12)
    fig.savefig(r/'comparison.png',dpi=180);fig.savefig(r/'comparison.pdf');plt.close(fig)
    files=[r/'study/analysis.json',r/'comparison.png',r/'comparison.pdf']
    (r/'figure_provenance.json').write_text(json.dumps(dict(sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='All108 measured rows from frozen randomized-order saved-input study. Geometry is12 targets, timing36 repeated calls per method; negative fixed-K low-cost refusals retained.'),indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
