#!/usr/bin/env python3
"""Descriptive whole-batch plot: every fixed method, no omitted refusals."""
import hashlib,json
from fractions import Fraction as F
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];E=R/'experiments/useful_expiry_certificate_20261004';P=R/'results'/E.name;Q=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 policy=read(P/'policy_frozen.json');summary=read(P/'summary_local.json');audit=read(P/'audit_test_sheng.json');methods=['function','deadline','cone'];colors=['#2878b5','#e68625','#279351'];fig,axes=plt.subplots(1,3,figsize=(13,4.5))
 for i,m in enumerate(methods):
  v=policy['methods'][m];risk=float(F(*v['conditional_upper']));utility=float(F(*v['utility']['lower']));axes[0].bar(i,risk,color=colors[i]);axes[1].bar(i,utility,color=colors[i]);axes[0].text(i,risk-.006,str(v['failed_authorized_episodes'])+'/'+str(v['authorized_episodes']),ha='center',va='top',color='white',fontsize=9);axes[1].text(i,utility+.015,str(v['utility']['useful'])+'/180',ha='center',fontsize=9)
  rows=[x for x in audit['risk_labels'] if x['method']==m];ys=[x['progress_um']/1e6 for x in rows if x['progress_um'] is not None];xs=[i+(j-(len(ys)-1)/2)*.013 for j in range(len(ys))];axes[2].scatter(xs,ys,color=colors[i],s=20,alpha=.75);axes[2].text(i,-.035,'accepted' if v['accepted'] else 'refused',ha='center',fontsize=9)
 axes[0].axhline(.05,color='black',linestyle='--',label='risk target 0.05');axes[0].set_title('Certification: safety upper bound',fontsize=10);axes[0].set_ylim(0,max(.1,max(float(F(*policy['methods'][m]['conditional_upper'])) for m in methods)+.04));axes[0].set_ylabel('Conditional episode failure probability')
 axes[1].axhline(.25,color='black',linestyle='--',label='utility target 0.25');axes[1].set_title('Certification: usefulness lower bound',fontsize=10);axes[1].set_ylim(0,1);axes[1].set_ylabel('Useful complete episodes / all planned episodes')
 axes[2].axhline(.05,color='black',linestyle='--',label='useful progress 0.05 m');axes[2].set_title('All held-out recorded progress',fontsize=10);axes[2].set_ylabel('Recorded projected progress (m)');axes[2].set_ylim(bottom=-.05)
 for ax in axes:ax.set_xticks(range(3),methods);ax.legend(fontsize=8,loc=('center left' if ax is axes[2] else 'upper left'));ax.grid(axis='y',alpha=.18)
 fig.suptitle('Six fixed exact tests; confidence requires joint IID scenes and execution',fontsize=11);fig.tight_layout();out=Q/'all_methods_layout.png';assert not out.exists();fig.savefig(out,dpi=150);plt.close(fig)
 receipt=dict(summary_sha256=sha(P/'summary_local.json'),policy_sha256=sha(P/'policy_frozen.json'),test_audit_sha256=sha(P/'audit_test_sheng.json'),figure_sha256=sha(out),all_methods=methods,descriptive_plot_only=True)
 target=Q/'figure_layout_inputs.json';assert not target.exists();target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
