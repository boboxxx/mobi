import json
from fractions import Fraction as F
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/transactions_diagnostic_20261011'
def main():
    first=json.loads((ROOT/'results/action_window_reference_20261011/local/scientific.json').read_text())
    audit=json.loads((OUT/'audit_local.json').read_text())
    fig,axes=plt.subplots(1,3,figsize=(12.6,4.1))
    names=['Nominal\nmodel','Robust\nwindow','Robust\nprefix','Union\nbound']
    keys=['nominal_window','robust_window','robust_prefix','robust_union']
    values=[first['summary']['methods'][k]['accepted'] for k in keys]
    violations=[first['summary']['methods'][k]['budget_violating_queries'] for k in keys]
    axes[0].bar(names,values,color=['#b96f3f','#306f8c','#739eae','#93afb6'])
    for i,(v,b) in enumerate(zip(values,violations)):
        axes[0].text(i,v+2,'%d\nexceed:%d'%(v,b),ha='center',fontsize=8)
    axes[0].set_ylim(0,140);axes[0].set_ylabel('Accepted queries / 612')
    axes[0].set_title('One partial observation',fontsize=11)
    minimum=float(F(audit['minimum_risk_witness']['minimum_worst_model_risk']))
    axes[1].bar(['Highest tested\nbudget','Best robust\nhistory risk'],[.1,minimum],color=['#8ca4b4','#b96f3f'])
    for i,v in enumerate([.1,minimum]):axes[1].text(i,v+.004,'%.2f%%'%(100*v),ha='center',fontsize=10)
    axes[1].set_ylim(0,.155);axes[1].set_ylabel('Conditional discrete conflict risk')
    axes[1].set_title('All 9,792 history queries refuse',fontsize=11)
    selected=[x for x in audit['oracle_reference'] if x['alpha']=='1/20']
    axes[2].bar(['0 ticks','1 tick','2 ticks'],[x['accepted'] for x in selected],color='#306f8c')
    for i,x in enumerate(selected):axes[2].text(i,x['accepted']+.8,'%d / %d'%(x['accepted'],x['query_count']),ha='center',fontsize=9)
    axes[2].set_ylim(0,55);axes[2].set_ylabel('Feasible oracle state/age/action combinations')
    axes[2].set_xlabel('Modeled use fee; alpha = 5%')
    axes[2].set_title('Exact source-state oracle only',fontsize=11)
    for ax in axes:ax.spines[['top','right']].set_visible(False);ax.tick_params(labelsize=9)
    fig.suptitle('Known-family synthetic diagnostics — no CARLA or real-traffic safety claim',fontsize=12)
    fig.tight_layout(rect=(0,0,1,.93))
    fig.savefig(OUT/'mechanism_diagnostics.png',dpi=180)
    plt.close(fig)

if __name__=='__main__':main()
