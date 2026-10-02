import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--study',default='study');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();s=json.loads((a.results/a.study/'analysis.json').read_bytes())
    methods=['fixed_strict','fixed_forward','fixed_terminal','coarse_forward','coarse_terminal','fine_forward','fine_terminal'];fig,axes=plt.subplots(1,2,figsize=(13,4.7))
    for k,preset in enumerate(['standard','slow','blackout']):
        values=[];covered=[]
        for m in methods:
            rows=[r for r in s['rows'] if r['method']==m and r['preset']==preset]
            values.append(100*sum(r['fresh_admission'] for r in rows)/len(rows))
            covered.append(100*np.mean([r['coverage'] for r in s['coverage'] if r['method']==m and r['preset']==preset]))
        axes[0].bar(np.arange(7)+(k-1)*.24,values,width=.24,label=preset)
        axes[1].bar(np.arange(7)+(k-1)*.24,covered,width=.24,label=preset)
    for ax,title in zip(axes,['Fresh admissions / all transmitted frames','Mean duration with 200ms action reserve']):
        ax.set_xticks(range(7));ax.set_xticklabels(methods,rotation=45,ha='right');ax.set_ylabel('Percent');ax.set_ylim(0,100);ax.set_title(title);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes[0].legend();fig.suptitle('sheng: '+a.study+'; modeled FIFO links; warm root\nConditional physical contract, stationary body; no continuous driving claim',fontsize=11)
    fig.tight_layout();fig.savefig(a.out,dpi=180);plt.close(fig)
if __name__=='__main__':main()
