"""Presentation of primary and explicitly post-analysis results; no fitting."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args()
    primary=json.loads((a.results/'analysis/report.json').read_text())['methods']
    realized=json.loads((a.results/'tick_realization.json').read_text())['methods']
    names=['constant','state'];labels=['Constant','State'];colors=['#627482','#087f8c']
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(12.8,4.4))
    b=axes[0].bar(labels,[primary[k]['joint_exceedances'] for k in names],color=colors,width=.55)
    axes[0].bar_label(b,labels=['0 / 400','7 / 400'],padding=5)
    axes[0].set(title='Primary held-out result',ylabel='Joint exceedances',ylim=(0,10))
    for i,k in enumerate(names):
        axes[0].text(i,8.8,'95%% upper: %.2f%%'%(100*primary[k]['upper_failure_95']),ha='center',fontsize=9)
    for x,key,label in [(-.18,'raw','Raw bound'),(.18,'ticks','After tick enlargement')]:
        values=[1000*(primary[k]['median_predicted']['stop_s'] if key=='raw' else realized[k]['median_stop_s']) for k in names]
        b=axes[1].bar([i+x for i in range(2)],values,width=.34,label=label,color=colors if key=='raw' else ['#b8c3cb','#93c9cc'])
        axes[1].bar_label(b,fmt='%.0f',padding=4)
    axes[1].set(xticks=[0,1],xticklabels=labels,title='Median stopping-time bound',ylabel='Milliseconds',ylim=(0,285))
    axes[1].legend(frameon=False,fontsize=8,loc='upper center')
    b=axes[2].bar(labels,[primary[k]['counterfactual_admissions'] for k in names],color=colors,width=.55)
    axes[2].bar_label(b,labels=['400 / 400','400 / 400'],padding=5)
    axes[2].set(title='Fixed-region admission check',ylabel='Counterfactual admissions',ylim=(0,480))
    fig.text(.5,.065,'Tick enlargement is post-analysis on the same test data; primary failures remain reported.',ha='center',fontsize=10)
    fig.text(.5,.02,'Fixed episode law, sampled finite window; no evidence-guided driving or physical safety guarantee.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.12,1,1));fig.savefig(a.results/'summary.png',dpi=180);fig.savefig(a.results/'summary.pdf');plt.close(fig)


if __name__=='__main__':main()
