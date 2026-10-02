import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();s=json.loads((a.results/'joint_bounds.json').read_bytes());fig,ax=plt.subplots(figsize=(10,7.7))
    for j,r in enumerate(s['rows']):
        low=r['lower_us']/1000;high=r['upper_us']/1000;color='#d6604d' if low==0 else '#2166ac';ax.plot([low,high],[j,j],color=color,lw=3);ax.scatter([low,high],[j,j],c=[color,color],marker='|',s=130)
    ax.set_yticks(range(18));ax.set_yticklabels([r['run'].replace('c0_view0_','c0 ').replace('c2_view0_','c2 ')+' / '+str(r['index']) for r in s['rows']],fontsize=9);ax.invert_yaxis();ax.set_xlim(-10,590);ax.axvline(200,color='gray',ls='--',label='200ms action reserve (zero delivery age)');ax.grid(axis='x',alpha=.2);ax.set_xlabel('Lifetime from source reference (ms)');ax.set_title('Certified lower bound — feasible hidden-trajectory upper bound\nOriginal received dictionaries; conditional stationary rectangle task',fontsize=11);ax.legend(loc='lower left',fontsize=8);fig.tight_layout();fig.savefig(a.results/'joint_bounds.png',dpi=180);plt.close(fig)
if __name__=='__main__':main()
