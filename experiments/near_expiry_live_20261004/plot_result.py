"""All18 physical-time trajectories; post-result display only."""
import gzip,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/near_expiry_live_20261004'
def main():
 fig,axes=plt.subplots(3,3,figsize=(12,8),sharex=True,sharey=True,constrained_layout=True)
 ctx=json.loads((P/'capture/context.json').read_bytes());road=np.array(ctx['basis']['road']);inputs={};names={'vehicle.audi.a2':(0,'Audi target'),'vehicle.diamondback.century':(1,'Bicycle target'),'walker.pedestrian.0001':(2,'Walker target')}
 for o in json.loads((P/'capture/outcomes.json').read_bytes()):
  path=P/'capture'/o['file'];inputs[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();d=json.loads(gzip.decompress(path.read_bytes()));request=d['request'];rows=d['rows'];i,name=names[request['blueprint']];j=abs(request['start_x_m'])-6
  if not rows:axes[i,j].text(.5,.5,'Capture failed',transform=axes[i,j].transAxes);continue
  first=np.array(rows[0]['own']['center']);progress=[float((np.array(r['after']['center'])-first)@road[:,0]) for r in rows];times=[(r['step']+1)*.05 for r in rows];method=request['method']
  axes[i,j].plot(times,progress,label='function' if method=='function' else 'compact deadline',color='#1664a5' if method=='function' else '#db7a16',linestyle='-' if method=='function' else '--',linewidth=1.7,zorder=1 if method=='function' else 2)
 for i in range(3):
  for j in range(3):
   ax=axes[i,j];ax.axvspan(1.5,2.5,color='#d86464',alpha=.15);ax.axvspan(8.,10.,color='#777777',alpha=.09);ax.set_title(list(names.values())[i][1]+' / start '+str(j+6)+'m',fontsize=10);ax.grid(alpha=.18);ax.set_ylim(-.05,1.6);ax.set_xlim(0,10)
   if j==0:ax.set_ylabel('Forward progress (m)')
   if i==2:ax.set_xlabel('CARLA physical time (s)')
 axes[0,0].legend(loc='upper left',fontsize=8)
 fig.suptitle('Near-hazard finite physical loop / 20ms modeled propagation\nRed: source packet dropout; gray: final full brake; no policy risk qualification',fontsize=11)
 fig.savefig(P/'physical_progress.png',dpi=180);fig.savefig(P/'physical_progress.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
 (P/'figure_inputs.json').write_text(json.dumps(dict(input_sha256=inputs,scope='All18 planned trajectories; failures retained; no radio or risk claim.'),indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
