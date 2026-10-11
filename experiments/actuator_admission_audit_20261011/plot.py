"""Publication figures from all declared episodes, with no omitted failures."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path('results/actuator_route_40s_20261011');a=json.loads((p/'analysis_sheng.json').read_bytes());b=json.loads(Path('results/actuator_admission_20261011/analysis_sheng.json').read_bytes())
labels=['Away −0.4','Away +0.4','Clear −0.4','Clear +0.4','Enters −0.4','Enters +0.4'];methods=['history','snapshot'];scenes=[('cross_away',0),('cross_away',1),('clear_stay',2),('clear_stay',3),('approach_stop',4),('approach_stop',5)]
# Pair identifiers are recorded in the frozen plans; use their sorted order.
pairs=sorted(set(e['pair'] for e in a['episodes']));assert len(pairs)==6
fig,axes=plt.subplots(1,2,figsize=(11,4.3),gridspec_kw={'width_ratios':[2.2,1]})
for j,method in enumerate(methods):
 es=[next(e for e in a['episodes'] if e['pair']==pair and e['method']==method) for pair in pairs];axes[0].bar(np.arange(6)+(j-.5)*.35,[e.get('max_progress_m',0) for e in es],width=.35,label=method.capitalize(),color=['#247a9e','#d58532'][j])
axes[0].axhline(11,ls='--',color='black',lw=.8,label='11 m route');axes[0].set_xticks(range(6),labels,rotation=25,ha='right');axes[0].set_ylabel('Maximum physical progress (m)');axes[0].set_title('Fixed 40 s task: all six scene pairs');axes[0].legend(fontsize=8)
x=np.arange(2)
for j,(name,analysis) in enumerate([('30 s',b),('40 s',a)]):
 vals=[analysis['summary']['methods'][m]['clear_route_completed'] for m in methods];axes[1].bar(x+(j-.5)*.32,vals,.32,label=name,color=['#b3bdc5','#367753'][j])
axes[1].set_xticks(x,['History','Snapshot']);axes[1].set_ylim(0,4.7);axes[1].set_yticks(range(5));axes[1].set_ylabel('Completed clear-road routes / 4');axes[1].set_title('Separate task specifications');axes[1].legend(fontsize=8)
fig.suptitle('CARLA physical development trials with virtual queues; no risk certificate',fontsize=10);fig.tight_layout();fig.savefig(p/'physical_routes.png',dpi=180);fig.savefig(p/'physical_routes.pdf');plt.close(fig)
