#!/usr/bin/env python3
"""Descriptive tables/figures from the actual completed study; no inferred runs."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
METHODS=['fixed','fine','scalar','aug_scalar','aug_fine']
LABELS=['Fixed region','Fine set','Scalar erosion','Extra rays\n+ scalar','Extra rays\n+ fine set']
COLORS=['#42566b','#7294a8','#8b7d6b','#bd6029','#367b6e']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def describe(xs):return dict(min=float(np.min(xs)),median=float(np.median(xs)),p95=float(np.quantile(xs,.95)),max=float(np.max(xs)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results;s=json.loads((r/'fifo_corrected.json').read_bytes());w=json.loads((r/'witness_local.json').read_bytes())
    for stem in ['audit','witness']:assert (r/(stem+'_local.json')).read_bytes()==(r/(stem+'_sheng.json')).read_bytes()
    assert json.loads((r/'audit_local.json').read_bytes())['root_fifo_occupancy_charged']
    out=dict(groups=[],by_run=[],augmentation={},joint_bounds=w['joint'],input_sha256={n:sha(r/n) for n in ['fifo_corrected.json','study/analysis.json','audit_local.json','witness_local.json']},scope='Descriptive recorded timings/paid modeled link outcomes after correcting initial root source/link occupancy. Six saved repeated-geometry histories, three timing repeats; no independent-scene confidence intervals, live link or moving control claim.')
    for preset in ['standard','slow','blackout']:
        for method in METHODS:
            xs=[x for x in s['rows'] if x['preset']==preset and x['method']==method];cs=[x for x in s['coverage'] if x['preset']==preset and x['method']==method];item=dict(preset=preset,method=method,attempts=len(xs),received=sum(not x['dropped'] for x in xs),geometry=sum(x['horizon_us']>0 for x in xs),fresh_admissions=sum(x['fresh_admission'] for x in xs),authority_ticks=sum(x['current_authority'] for x in xs),covered_us=sum(x['covered_us'] for x in cs),window_us=sum(x['end_us']-x['start_us'] for x in cs),wire_bytes=sum(x['bytes'] for x in xs),verification_ms=describe([x['verification_ms'] for x in xs if not x['dropped']]),total_ms=describe([x['total_ms'] for x in xs]),coverage_each_repeat=[sum(x['covered_us'] for x in cs if x['repeat']==j)/sum(x['end_us']-x['start_us'] for x in cs if x['repeat']==j) for j in range(3)])
            item['duration_coverage']=item['covered_us']/item['window_us'];out['groups'].append(item)
            for run in [c['run'] for c in s['contexts']]:
                xx=[x for x in xs if x['run']==run];out['by_run'].append(dict(run=run,preset=preset,method=method,geometry=sum(x['horizon_us']>0 for x in xx),admissions=sum(x['fresh_admission'] for x in xx),horizons_us=sorted({x['horizon_us'] for x in xx})))
    out['augmentation']=dict(calls=len(s['augmentation']),supported=sum(x['supported'] for x in s['augmentation']),generation_ms=describe([x['generation_ms'] for x in s['augmentation']]),extra_rays=describe([x['stats']['extra_rays'] for x in s['augmentation']]),original_rays=describe([x['stats']['original_rays'] for x in s['augmentation']]),augmented_rays=describe([x['stats']['rays'] for x in s['augmentation']]),warm_prefix_aggregate_ms=describe([c['warm_prefix_ms'] for c in s['contexts']]))
    out['bounds']=dict(queries=len(w['joint']),with_upper=w['queries_with_verified_upper'],surviving_candidates=w['surviving_witnesses'],segment_checks=w['segment_checks'],maximum_gap_us=max(x['gap_us'] for x in w['joint'] if x['gap_us'] is not None),maximum_relative_loss_bound=max(x['relative_loss_bound'] for x in w['joint'] if x['relative_loss_bound'] is not None))
    (r/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained');groups=[x for x in out['groups'] if x['preset']=='standard'];xx=np.arange(5)
    ax[0].bar(xx-.18,[x['geometry'] for x in groups],width=.36,color=COLORS,alpha=.35,label='Geometric certificates');ax[0].bar(xx+.18,[x['fresh_admissions'] for x in groups],width=.36,color=COLORS,label='Timely 200 ms grants')
    for j,x in enumerate(groups):
        ax[0].text(j-.18,x['geometry']+4,str(x['geometry']),ha='center',fontsize=9);ax[0].text(j+.18,x['fresh_admissions']+4,str(x['fresh_admissions']),ha='center',fontsize=9)
    ax[0].set(xticks=xx,xticklabels=LABELS,ylim=(0,405),ylabel='Count / 360 attempts',title='More proof success, less usable permission');ax[0].legend(frameon=False,fontsize=8)
    for j,method in enumerate(METHODS):
        vals=[100*next(x['duration_coverage'] for x in out['groups'] if x['method']==method and x['preset']==preset) for preset in ['standard','slow','blackout']]
        ax[1].bar(np.arange(3)+(j-2)*.16,vals,width=.15,color=COLORS[j],label=LABELS[j].replace('\n',' '))
    ax[1].set(xticks=np.arange(3),xticklabels=['20 Mbps','0.5 Mbps','20 Mbps + loss'],ylabel='Certified action duration / source window (%)',title='Actual service charged; links modeled');ax[1].legend(frameon=False,fontsize=8)
    fig.suptitle('Class-specific evidence: six saved histories, three timing repeats',fontsize=13)
    for ext in ['png','pdf']:fig.savefig(r/('paid_outcomes.'+ext),dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained');runs=sorted({x['run'] for x in w['joint']})
    for j,run in enumerate(runs):
        rows=[x for x in w['joint'] if x['run']==run];assert len({(x['lower_us'],x['upper_us']) for x in rows})==1;x=rows[0];lo=x['lower_us']/1000;hi=x['upper_us']/1000;ax.plot([lo,hi],[j,j],color='#7b8893',lw=3);ax.scatter([lo],[j],color='#367b6e',s=55,zorder=3);ax.scatter([hi],[j],color='#bd6029',marker='x',s=65,zorder=3);ax.text(lo-7,j,f'{lo:.3f}',ha='right',va='center',fontsize=9);ax.text(hi+7,j,f'{hi:.0f}',va='center',fontsize=9)
    ax.set(yticks=range(len(runs)),yticklabels=[x.replace('_view0','').replace('_',' ')+' (3 queries)' for x in runs],xlabel='Lifetime from source reference (ms)',xlim=(420,820),title='Augmented information: certified lower / surviving candidate upper');ax.grid(axis='x',alpha=.2)
    for ext in ['png','pdf']:fig.savefig(r/('augmented_bounds.'+ext),dpi=180)
    plt.close(fig)
    print(json.dumps(dict(groups=len(out['groups']),rows=len(s['rows']),bounds=out['bounds'],summary_sha256=sha(r/'summary.json'))))
if __name__=='__main__':main()
