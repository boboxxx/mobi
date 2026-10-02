#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);a=ap.parse_args()
    current=json.loads((a.results/'validation.json').read_bytes());old=json.loads((a.previous/'validation.json').read_bytes())
    names=['c0_view0_reuse_fixed','c0_view0_reuse_rate20','c2_view0_reuse_rate20']
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for index,identity in enumerate(['drive_025','drive_039']):
        ax=axes[index];x=np.arange(3);width=.35
        before=[next(z for z in old['summaries'] if z['run']==n and z['id']==identity and z['method']=='greedy_fixed') for n in names]
        after=[next(z for z in current['summaries'] if z['run']==n and z['id']==identity and z['method']=='stream_fixed') for n in names]
        # Old full all-stage cost includes actual acquisition and its full bytes.
        raw=json.loads((a.previous/'study/analysis.json').read_bytes())
        cost=[np.median([sum(r[f] for f in ['acquisition_ms','generation_ms','verification_ms','wire_ms']) for r in raw['rows'] if r['run']==n and r['id']==identity and r['method']=='greedy_fixed']) for n in names]
        ax.bar(x-width/2,cost,width,label='On demand, JSON')
        ax.bar(x+width/2,[z['total_ms_median'] for z in after],width,label='FIFO maintenance, compressed')
        ax.axhline(250,color='black',linestyle='--',linewidth=1,label='Largest passing age (50 ms ticks)')
        ax.set_title(identity+' (geometrically recoverable subset)')
        ax.set_xticks(x,['c0 fixed','c0 rate20','c2 rate20']);ax.set_ylabel('Target observation to available proof (ms)')
        for i,z in enumerate(after):ax.text(i+width/2,z['total_ms_median']+50,str(z['action_passes'])+'/3 timely',ha='center',fontsize=8)
        ax.set_ylim(0,max(cost)*1.14)
    axes[0].legend(fontsize=8,loc='upper left')
    fig.suptitle('Fixed 475 ms proof / 200 ms reserve: 6/12 targets recover geometry; 2/36 requests timely',fontsize=11)
    figure=a.results/'recovery_timing.png';fig.savefig(figure,dpi=160);plt.close(fig)
    files=[Path(__file__).resolve(),a.results/'validation.json',a.previous/'validation.json',a.previous/'study/analysis.json',figure]
    root=Path(__file__).resolve().parents[2]
    report=dict(file_sha256={str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},matplotlib_version=matplotlib.__version__,scope='Rendered locally from unchanged archived sheng measurements; plotted recoverable subset only; six temporally gapped targets and cold failures remain in full tables.')
    (a.results/'plot_provenance.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
