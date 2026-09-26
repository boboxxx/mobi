"""Aggregate paired results without selecting configurations by performance."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def bootstrap_cluster(df, delta, cluster, seed=402, repetitions=4000):
    groups=df.groupby(cluster)[delta].agg(['sum','count'])
    rng=np.random.default_rng(seed)
    ids=rng.integers(0,len(groups),size=(repetitions,len(groups)))
    means=groups['sum'].to_numpy()[ids].sum(axis=1)/groups['count'].to_numpy()[ids].sum(axis=1)
    low,high=np.quantile(means,[.025,.975])
    return dict(mean=float(df[delta].mean()),ci_low=float(low),ci_high=float(high),
                clusters=len(groups),observations=len(df),
                positive=int((df[delta]>1e-8).sum()),negative=int((df[delta]<-1e-8).sum()))


def main():
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);args=a.parse_args()
    root=Path(args.root);out=root/'analysis';out.mkdir(exist_ok=True)
    b=pd.read_csv(root/'bayes/paired.csv')
    bayes=[]
    for key,g in b.groupby(['family','q','budget']):
        for metric in ['exact_gain','pair_gain']:
            bayes.append(dict(zip(['family','q','budget'],key),metric=metric,
                              **bootstrap_cluster(g,metric,'seed')))
    bf=pd.DataFrame(bayes);bf.to_csv(out/'bayes_paired_ci.csv',index=False)
    df=pd.read_csv(root/'opv2v_self_filtered/per_frame.csv')
    d=pd.read_csv(root/'opv2v_self_filtered/diagnostics.csv')
    manifest=json.loads((root/'opv2v_self_filtered/manifest.json').read_text())
    caps={x['name']:x['budget'] for x in manifest['configurations']}
    assert np.all(df.planned_bytes <= df.config.map(caps))
    assert np.all(df.expected_tx_bytes <= df.planned_bytes+1e-7)
    assert np.all(df.regret >= -1e-7)
    assert df.gt_block.between(-1e-9,1+1e-9).all()
    assert df.match.between(-1e-9,1+1e-9).all()
    assert df.groupby(['frame','family','config']).size().eq(6).all()
    assert len(df)==manifest['eligible_frames']*2*len(caps)*6
    results=[]
    # Same-frame paired differences, then resample entire scenes.
    for metric in ['regret','gt_regret','gt_block','progress','expected_tx_bytes']:
        p=df.pivot_table(index=['frame','scene','split','family','config'],columns='method',values=metric).reset_index()
        for other in ['greedy_voi','pair_lookahead','coverage_ranking','confidence_broadcast']:
            p['delta']=p[other]-p.exact_subset
            for key,g in p.groupby(['split','family','config']):
                results.append(dict(zip(['split','family','config'],key),metric=metric,
                    comparison=f'{other}_minus_exact',**bootstrap_cluster(g,'delta','scene')))
    paired=pd.DataFrame(results);paired.to_csv(out/'opv2v_paired_ci.csv',index=False)
    diag={}
    for family,g in d[d.split=='evaluation'].groupby('family'):
        diag[family]=dict(frames=len(g),scenes=int(g.scene.nunique()),
            reference_differs=int((g.ego_action!=g.full_action).sum()),
            source_blockage=float(g.ego_gt_block.mean()),reference_blockage=float(g.full_gt_block.mean()),
            table_p50_ms=float(g.table_ms.quantile(.5)),table_p95_ms=float(g.table_ms.quantile(.95)),
            table_p99_ms=float(g.table_ms.quantile(.99)),
            removed_sender=int(g.removed_sender.sum()),removed_gt=int(g.removed_gt.sum()),
            max_abs_roll=float(g.abs_roll.max()),max_abs_pitch=float(g.abs_pitch.max()))
    verdict=dict(source_frames=manifest['source_frames'],eligible_frames=manifest['eligible_frames'],
                 excluded_frames=manifest['excluded_frames'],diagnostics=diag,
                 audit='All budget, probability-range, paired-count and nonnegative regret assertions passed.')
    (out/'audit.json').write_text(json.dumps(verdict,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(15,4.3))
    colors=['#3467a5','#bf592d','#3f8b67']
    labels=['Single requirement','Two requirements','Three requirements']
    for fam,col,lab in zip(['single_requirement','two_requirements','three_requirements'],colors,labels):
        g=bf[(bf.family==fam)&(bf.q==.8)&(bf.metric=='exact_gain')]
        axes[0].errorbar(g.budget,g['mean'],yerr=np.maximum(0,np.array([g['mean']-g.ci_low,g.ci_high-g['mean']])),
                         marker='o',label=lab,color=col,capsize=3)
    axes[0].set(xlabel='Message budget',ylabel='Exact minus singleton utility',
                title='A. Generated Bayesian models (q=0.8)')
    axes[0].legend(fontsize=8)
    s=pd.read_csv(root/'opv2v_self_filtered/summary.csv')
    for ax,family,title in zip(axes[1:],['route_prefix','lateral_stress'],
                               ['B. Recorded-route prefix probe','C. Lateral-alternative stress probe']):
        for method,color,style in [('confidence_broadcast','#888888','--'),('greedy_voi','#bf592d','--'),('exact_subset','#3467a5','-')]:
            g=s[(s.split=='evaluation')&(s.family==family)&(s.method==method)&(s.config.str.match(r'b\d+_q0\.8$'))].copy()
            g['budget']=g.config.str.extract(r'b(\d+)').astype(int)
            g=g.sort_values('budget')
            ax.plot(g.budget,g.regret,marker='o',color=color,linestyle=style,label=method)
        ax.set(xlabel='Total application bytes / decision',ylabel='Reference decision regret (proxy)',title=title)
        ax.legend(fontsize=7)
    fig.suptitle('Feasibility pilot on sheng — mechanism test and open-loop probes; not driving safety',fontsize=12)
    fig.tight_layout()
    fig.savefig(out/'feasibility.png',dpi=180)
    fig.savefig(out/'feasibility.pdf')
    print(json.dumps(verdict,indent=2))
    print('MAIN PAIRED RESULTS')
    print(paired[(paired.split=='evaluation')&(paired.metric=='regret')&
                 (paired.comparison=='greedy_voi_minus_exact')].to_string(index=False))


if __name__=='__main__':main()
