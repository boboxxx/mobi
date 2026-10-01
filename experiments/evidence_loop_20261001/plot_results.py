import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=json.loads((a.results/'repair/report.json').read_text());row=r['rows'][0];colors=['#677b88','#007e89'];labels=['Full compression','Local repair']
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False});fig,axes=plt.subplots(1,2,figsize=(10,4.6))
    for ax,vals,title,unit,limit in [(axes[0],[r['median_ms'][k] for k in ['compressed','repair']],'Proof generation, paired median','Milliseconds',850),(axes[1],[row[k+'_bytes']/1000 for k in ['compressed','repair']],'Serialized message cost','Kilobytes (decimal)',100)]:
        b=ax.bar(labels,vals,color=colors,width=.55);ax.bar_label(b,fmt='%.1f',padding=5);ax.set(title=title,ylabel=unit,ylim=(0,limit))
    axes[0].axhline(400,color='#a35235',ls='--',lw=1,label='400 ms full geometric lifetime');axes[0].legend(frameon=False,fontsize=9)
    fig.text(.5,.07,'One identified archived transition; 8 alternating-order repeats, not independent scenarios.',ha='center',fontsize=10)
    fig.text(.5,.025,'Acquisition, receiver, transport and action time are additional. Fresh repaired driving has not been evaluated.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.13,1,1));fig.savefig(a.results/'repair_comparison.png',dpi=180);fig.savefig(a.results/'repair_comparison.pdf');plt.close(fig)


if __name__=='__main__':main()
