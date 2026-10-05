#!/usr/bin/env python3
"""All fixed diagnosis cells, with no excluded baseline or transformed units."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];P=R/'results'/Path(__file__).resolve().parent.name
s=json.loads((P/'summary_local.json').read_text());variants=['period3_deferred','period3_immediate','period2_deferred','period2_immediate'];methods=['function','deadline','cone'];classes=['vehicle.audi.a2','vehicle.bh.crossbike','walker.pedestrian.0001']
classes=sorted(set(x['blueprint'] for x in s['episodes']))
fig,axs=plt.subplots(1,3,figsize=(12,4.2),sharey=True)
for ax,cls in zip(axs,classes):
 for j,m in enumerate(methods):
  ys=[next(x['forward_m'] for x in s['episodes'] if x['blueprint']==cls and x['method']==m and x['variant']==v) for v in variants]
  ax.bar([i+(j-1)*.24 for i in range(4)],ys,.24,label=m)
 ax.set_title(cls,fontsize=10);ax.set_xticks(range(4),['150ms\ndeferred','150ms\nimmediate','100ms\ndeferred','100ms\nimmediate']);ax.set_ylim(0,.35);ax.grid(axis='y',alpha=.2)
axs[0].set_ylabel('Recorded forward progress (m / 3 s)');axs[-1].legend(fontsize=8);fig.suptitle('Receiver scheduling diagnosis: all 36 single-run cells; no risk certificate',fontsize=11);fig.tight_layout()
o=P/'receiver_budget_all_cells.png';assert not o.exists();fig.savefig(o,dpi=150);plt.close(fig)
receipt=dict(summary_sha256=hashlib.sha256((P/'summary_local.json').read_bytes()).hexdigest(),figure_sha256=hashlib.sha256(o.read_bytes()).hexdigest(),all_cells=36,post_result_descriptive_only=True)
(P/'figure_inputs.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
