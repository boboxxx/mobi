#!/usr/bin/env python3
"""Show all fixed methods and every completed held-out episode."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads((P/'summary_sheng.json').read_bytes());c=json.loads((P/'policy_frozen.json').read_bytes());assert s['policy_sha256']==sha(P/'policy_frozen.json')
 out=P/'all_methods_layout.png';receipt=P/'figure_layout_inputs.json';assert not out.exists() and not receipt.exists()
 methods=['function','deadline','cone'];fig,ax=plt.subplots(1,3,figsize=(13,4.3));colors=['#2875b8','#c88c18','#2d9973']
 for i,m in enumerate(methods):
  x=c['methods'][m];u=x['conditional_upper'][0]/x['conditional_upper'][1];ax[0].bar(i,u*100,color=colors[i]);ax[0].text(i,u*100+.6,f"{x['failed_authorized_episodes']}/{x['authorized_episodes']} failures",ha='center',fontsize=8)
  z=next(v for v in s['cells'] if v['method']==m);ys=[v['forward_m'] for v in z['episodes'] if v['status']=='captured'];ax[1].scatter([i]*len(ys),ys,s=16,alpha=.65,color=colors[i]);ax[1].text(i, max(ys+[0])+.08, f"{z['captured']}/24 captured",ha='center',fontsize=8);ax[2].bar(i,z['actual_wire_bytes_total']/1000,color=colors[i])
 ax[0].axhline(5,color='black',ls='--',lw=1,label='Fixed 5% target');ax[0].set_ylabel('Conditional failure upper bound (%)');ax[0].set_ylim(0,max(10,ax[0].get_ylim()[1]+4));ax[0].legend(fontsize=8);ax[0].set_title('180 planned certification episodes / method',fontsize=9)
 ax[1].set_ylim(-.01,max(.2,max(v['completed_episode_forward_m'].get('max',0) for v in s['cells'])+.2));ax[1].set_ylabel('Completed episode forward progress (m)');ax[1].set_title('All held-out episodes; certificate gate applied',fontsize=9);ax[2].set_ylabel('Actual serialized source payload (kB)');ax[2].set_title('24 unpaired planned test episodes / method',fontsize=9)
 for a in ax:a.set_xticks(range(3),methods);a.grid(axis='y',alpha=.2)
 fig.suptitle('Finite parked-target prototype: joint IID assumption; modeled link; no road-risk guarantee',fontsize=10);fig.tight_layout();fig.savefig(out,dpi=180);plt.close(fig)
 receipt.write_text(json.dumps(dict(input_sha256={str(p.relative_to(ROOT)):sha(p) for p in (P/'summary_sheng.json',P/'policy_frozen.json')},figure_sha256=sha(out),all_methods=methods,scope='All methods shown; no paired/causal comparison and no query independence.'),indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
