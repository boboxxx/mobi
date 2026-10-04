"""Deterministic local exemplars with episode-excluded scale fitting and guard."""
import math,sys
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/state_predictor_20261004'))
from predictor import features
K=8;LOCAL=32;MIN_SCALE_UM=50000

def anchor_um(hulls,layout):
    f,a=features(hulls,layout)
    if f is None:return None,None
    return f,[int(round(float(x)*1000000)) for x in a]
def roundmean(vals):return [round(Fraction(sum(v[j] for v in vals),len(vals))) for j in (0,1)]
def upnorm(v):
    n=sum(int(x)**2 for x in v);r=math.isqrt(n);return r+(r*r<n)
def distances(z,templates):
    # Stabilize numeric tie ordering, not geometric/coverage calculations.
    return np.round(np.sum((templates-z)**2,axis=1),9)
def fit(rows,labels):
    ff=[];offset=[];eps=[];ids=[];layouts=[]
    for r in rows:
        f,a=anchor_um(r['hulls_cm'],r['layout'])
        if f is None:continue
        truth=[round(Fraction.from_float(float(x))*1000000) for x in labels[r['id']]]
        ff.append(f);offset.append([truth[j]-a[j] for j in (0,1)]);eps.append(r['episode_id']);ids.append(r['id']);layouts.append(r['layout'])
    X=np.asarray(ff);mu=X.mean(0);sd=np.maximum(X.std(0),.001);Z=(X-mu)/sd;offset=np.asarray(offset,dtype=np.int64);loo_single=[];loo_modes=[];nn=[]
    for i,z in enumerate(Z):
        dd=distances(z,Z);eligible=[j for j in range(len(Z)) if eps[j]!=eps[i] and layouts[j]==layouts[i]];eligible.sort(key=lambda j:(float(dd[j]),ids[j]));ii=eligible[:K];assert len(ii)==K
        nn.append(float(dd[ii[0]]));av=roundmean(offset[ii].tolist());loo_single.append(upnorm([int(offset[i,j])-av[j] for j in (0,1)]));loo_modes.append(min(upnorm((offset[i]-offset[j]).tolist()) for j in ii))
    ranges=X.max(0)-X.min(0);pad=np.maximum(.1*ranges,1e-6)
    return dict(k=K,local=LOCAL,min_scale_um=MIN_SCALE_UM,mean=mu.tolist(),scale=sd.tolist(),templates_z=Z.tolist(),offsets_um=offset.tolist(),ids=ids,episodes=eps,layouts=layouts,guard_min=(X.min(0)-pad).tolist(),guard_max=(X.max(0)+pad).tolist(),guard_nearest_squared=max(nn),loo_single_um=loo_single,loo_modes_um=loo_modes,training_rows=len(Z),scope='Hull-only exemplar offsets; scale from same-layout, different-episode training residuals, not a certified conditional density.')
def prepare(m):
    return dict(mean=np.asarray(m['mean']),scale=np.asarray(m['scale']),z=np.asarray(m['templates_z']),offset=np.asarray(m['offsets_um'],dtype=np.int64),lo=np.asarray(m['guard_min']),hi=np.asarray(m['guard_max']))
def predict(hulls,layout,m,prepared=None):
    f,a=anchor_um(hulls,layout)
    if f is None:return dict(status='refused',reason='empty_observation',centers_um=[],mean_um=None)
    t=prepared if prepared is not None else prepare(m)
    if np.any(f<t['lo']) or np.any(f>t['hi']):return dict(status='fallback',reason='outside_training_range',centers_um=[],mean_um=None)
    dd=distances((f-t['mean'])/t['scale'],t['z']);ii=[j for j,l in enumerate(m['layouts']) if l==layout];ii.sort(key=lambda j:(float(dd[j]),m['ids'][j]))
    if not ii or float(dd[ii[0]])>m['guard_nearest_squared']:return dict(status='fallback',reason='outside_episode_neighbor_support',centers_um=[],mean_um=None)
    picked=ii[:m['k']];near=ii[:m['local']];raw=[[a[k]+int(t['offset'][j,k]) for k in (0,1)] for j in picked];av=roundmean(raw);centers=sorted(set(map(tuple,raw)));scale={}
    for method,field in [('single','loo_single_um'),('modes','loo_modes_um')]:
        values=sorted(m[field][j] for j in near);rank=(9*len(values)+9)//10;scale[method]=max(m['min_scale_um'],values[rank-1])
    return dict(status='supported',reason='training_supported',centers_um=[list(v) for v in centers],mean_um=av,single_scale_um=scale['single'],modes_scale_um=scale['modes'],neighbor_ids=[m['ids'][j] for j in picked],nearest_squared=float(dd[ii[0]]))
