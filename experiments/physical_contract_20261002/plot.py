import json,math
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull,distance
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/physical_contract_20261002';a=json.loads((OUT/'analysis_sheng.json').read_bytes());r=json.loads((OUT/'capture/record.json').read_bytes());audit=json.loads((OUT/'audit_local.json').read_bytes());fig,axes=plt.subplots(1,2,figsize=(10,4.6))
for ax,bp in zip(axes,['vehicle.diamondback.century','vehicle.mercedes.sprinter']):
 eligible={x['id'] for x in audit['rows'] if x['any_center_outer_impossible']} if 'sprinter' in bp else None
 row=next(x for x in a['rows'] if x['blueprint']==bp and (eligible is None or x['id'] in eligible));m=next(x for x in r if x['id']==row['id']);c=np.array(m['center'])[:2]
 with np.load(OUT/'capture'/m['cloud_file']) as z:xyz=z['xyz'];raw=z['raw']
 own=xyz[raw['id']==m['actor_id'],:2]-c;ax.scatter(own[:,0],own[:,1],s=7,c='#2563eb',label='Actual actor LiDAR returns');ax.scatter([0],[0],marker='+',s=80,c='black',label='Declared actor center')
 if 'century' in bp:
  ax.add_patch(Circle((0,0),row['r_min'],facecolor='#f59e0b',edgecolor='#b45309',alpha=.2,label='Claimed opaque disk (0.55 m)'));w=np.array(row['proof_projected_local'])+m['query']-c;ax.scatter(w[0],w[1],s=70,marker='x',c='#dc2626',label='Empty ray crossing at probe plane');tile=np.array(row['tile_center_local'])+m['query']-c;ax.add_patch(Rectangle(tile-.05,.1,.1,fill=False,edgecolor='#dc2626',linewidth=2,label='Actual center tile excluded'));ax.set_title('Bicycle: contradicted inner core');ax.set_xlim(-1,1);ax.set_ylim(-1,1)
 else:
  ax.add_patch(Circle((0,0),row['r_max'],fill=False,edgecolor='#b45309',linewidth=2,label='Claimed outer radius (2.5 m)'));h=own[ConvexHull(own).vertices];d=distance.squareform(distance.pdist(h));i,j=np.unravel_index(np.argmax(d),d.shape);ax.plot(h[[i,j],0],h[[i,j],1],color='#dc2626',linewidth=2,label=f'Observed diameter {d[i,j]:.2f} m > 5 m');ax.set_title('Sprinter: no center fits claimed radius');ax.set_xlim(-3.5,3.5);ax.set_ylim(-3.5,3.5)
 ax.set_aspect('equal');ax.set_xlabel('World x relative to actor center (m)');ax.set_ylabel('World y relative to actor center (m)');ax.grid(alpha=.15);ax.legend(fontsize=7,loc='lower left')
fig.suptitle('Fresh CARLA observations falsify two physical premises',fontsize=13);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(OUT/('counterexamples.'+ext),dpi=180)
