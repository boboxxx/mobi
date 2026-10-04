"""Observable runtime only: XYZ, own odometry, registered class/context."""
import hashlib,json,math,sys,time,zlib
from fractions import Fraction as F
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/prospective_component_20261004'))
from fresh_io import frontend
from fresh_inference import state
from scores import load_models
sys.path.insert(0,str(ROOT/'experiments/action_expiry_20261004'))
from query_kernel import Evidence,decision
DT=50000;ACTION=300000

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(d):return json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pack(d):
 b=canonical(d);return zlib.compress(b+hashlib.sha256(b).digest(),6)
def unpack(w):
 b=zlib.decompress(w);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:]
 return json.loads(b[:-32])
def roundup(t):return ((t+DT-1)//DT)*DT
def source_link(source,acquisition,source_fee,nbytes,prop,free):
 begin=max(source+acquisition+source_fee,free);end=begin+(nbytes*8*1000000+20000000-1)//20000000
 return end+prop,end
def query_position(own,basis):
 p=(np.asarray(own['center'])-basis['anchor'])@np.asarray(basis['road'])
 return [int(round(v*1000000)) for v in p[:2]]
def action_radius(body):return math.ceil(math.sqrt(sum(e*e for e in body['extent']))*1000000)+245000
def own_mask(xyz,T,own,body):
 world=np.asarray(xyz,dtype=float)@np.asarray(T)[:3,:3].T+np.asarray(T)[:3,3]
 local=(world-own['location'])@np.asarray(own['matrix'])[:3,:3]
 assert body['rotation']==[0.,0.,0.]
 inside=np.all(abs(local-body['offset'])<=np.asarray(body['extent'])+.03,axis=1)
 return np.asarray(xyz)[~inside],inside
def thresholds(ctx,bp):return dict(supported=F(*ctx['registry'][bp]['supported_mean']),fallback_um=int(F(*ctx['registry'][bp]['fallback_um'])))
def evidence(obj,ctx):return Evidence(obj['hulls_cm'],ctx['catalog'][obj['blueprint']],obj['hypothesis'],thresholds(ctx,obj['blueprint']),'component_mean',obj['source_us'])
def encode(raw,T,own,body,ctx,bp,method,source_us,frame,models,background):
 xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');kept,mask=own_mask(xyz,T,own,body)
 # The frontend expects XYZ columns; all target labels/IDs remain unused.
 observable=np.empty(len(kept),dtype=[('x','<f4'),('y','<f4'),('z','<f4')])
 for j,k in enumerate(('x','y','z')):observable[k]=kept[:,j]
 gg,hh=frontend(observable,T,ctx['catalog'][bp],ctx['basis'],background,0)
 hyp=state(hh,0,bp,models,'component_mean')
 obj=dict(version=1,kind=method,blueprint=bp,source_us=source_us,frame=frame,context=sha_context(ctx))
 original=dict(obj,hulls_cm=hh,hypothesis=hyp)
 proposal=None
 if method=='function':obj.update(hulls_cm=hh,hypothesis=hyp)
 else:
  assert method=='deadline'
  proposal=evidence(original,ctx).query(query_position(own,ctx['basis']),action_radius(body)+150000)
  obj['proposal']={k:v for k,v in proposal.items() if k!='body_proofs'}
 return pack(obj),dict(original=original,source_proposal=proposal,masked_returns=int(mask.sum()),kept_xyz_sha256=hashlib.sha256(kept.tobytes()).hexdigest(),groups_cm=gg)
def sha_context(ctx):return hashlib.sha256(canonical(ctx)).hexdigest()
def decode(w,ctx):
 obj=unpack(w);assert obj['version']==1 and obj['context']==sha_context(ctx) and obj['blueprint'] in ctx['catalog'] and obj['kind'] in ('function','deadline')
 assert type(obj['source_us']) is int and obj['source_us']>=0 and type(obj['frame']) is int
 return dict(obj=obj,compiled=evidence(obj,ctx) if obj['kind']=='function' else None)
def choose(cache,own,body,ctx,now):
 if cache is None:return None,dict(geometry_eligible=False,deployment_authorized=False,reason='no_completed_evidence')
 obj=cache['obj'];q=query_position(own,ctx['basis']);r=action_radius(body)
 if obj['kind']=='function':p=cache['compiled'].query(q,r);domain=True
 else:
  p=obj['proposal'];n=sum((q[k]-p['query_um'][k])**2 for k in (0,1));d=math.isqrt(n)+(math.isqrt(n)**2<n)
  domain=d+r<=p['query_radius_um']
 gate=decision(p,now,ACTION);gate['query_domain_valid']=domain;gate['geometry_eligible']&=domain
 return p,gate
def relay(own,go):
 speed=math.hypot(*own['velocity'][:2])
 if not go:return 0.,1.
 return (.8 if speed<.3 else 0.),(min(.4,max(0.,.4*(speed-.3))) if speed>.35 else 0.)
