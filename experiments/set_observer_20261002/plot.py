#!/usr/bin/env python3
"""Static export from frozen source rows; preserve provenance next to figure."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results
    s=json.loads((r/'study/analysis.json').read_bytes());f=json.loads((r/'refined/analysis.json').read_bytes())
    groups=[[x for x in s['rows'] if x['method']==m] for m in ['fixed_K','position_set']]+[f['rows']]
    labels=['Fixed-K\n3 repeats','Position set\n3 repeats','Fine position set\n1 diagnostic repeat']
    fig,ax=plt.subplots(1,2,figsize=(10,3.8),layout='constrained');colors=['#566573','#2874a6','#1e8449']
    counts=[len({(x['run'],x['id']) for x in g if x['geometry']}) for g in groups]
    b=ax[0].bar(np.arange(3),counts,color=colors)
    ax[0].bar_label(b,labels=[str(n)+'/12' for n in counts]);ax[0].set_ylim(0,13);ax[0].set_ylabel('Targets with conditional geometry');ax[0].set_xticks(np.arange(3),labels);ax[0].set_title('Same available raw observations')
    for i,(g,c) in enumerate(zip(groups,colors)):
        ax[1].scatter(np.full(len(g),i),[x['total_ms'] for x in g],color=c,alpha=.45,s=19)
        ax[1].scatter(i,np.median([x['total_ms'] for x in g]),marker='_',s=300,color='black',linewidths=2)
    ax[1].axhline(250,color='#c0392b',ls='--',lw=1.2,label='Latest passing 50 ms age tick')
    ax[1].set_ylabel('Charged evidence age before tick rounding (ms)');ax[1].set_xticks(np.arange(3),labels);ax[1].set_title('Useful calls: 1/36, 0/36, 0/12');ax[1].legend(fontsize=8)
    for x in ax:x.spines[['top','right']].set_visible(False);x.tick_params(axis='x',labelsize=8)
    fig.suptitle('sheng: representation restores facts, but costs still defeat use',fontsize=12)
    fig.savefig(r/'comparison.png',dpi=180);fig.savefig(r/'comparison.pdf');plt.close(fig)
    hashes={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'study/analysis.json',r/'refined/analysis.json',r/'comparison.png',r/'comparison.pdf']}
    (r/'figure_provenance.json').write_text(json.dumps(dict(sha256=hashes,plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='All original rows; fine diagnostic has one repeat and is not a held-out method gain. Line assumes H≈475ms and200ms action reserve.'),indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
