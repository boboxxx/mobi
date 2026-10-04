"""Single-pack observable sources for fixed finite whole-episode certification."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('episode_fixed_observable_runtime',Path(__file__).resolve().parents[1]/'ego_expiry_live_20261004/runtime.py')
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
for name in dir(BASE):
 if not name.startswith('__'):globals()[name]=getattr(BASE,name)
from query_kernel import horizon,pose
DRIVE=60;BRAKE=40;PERIOD=3;DOMAIN_PAD=150005

def encode(raw,T,own,body,ctx,bp,method,source_us,frame,models,background):
 assert method in ('function','deadline','cone')
 xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');kept,mask=own_mask(xyz,T,own,body)
 observable=np.empty(len(kept),dtype=[('x','<f4'),('y','<f4'),('z','<f4')])
 for j,k in enumerate(('x','y','z')):observable[k]=kept[:,j]
 gg,hh=frontend(observable,T,ctx['catalog'][bp],ctx['basis'],background,0)
 hyp=state(hh,0,bp,models,'component_mean')
 header=dict(version=1,kind=method,blueprint=bp,source_us=source_us,frame=frame,context=sha_context(ctx))
 original=dict(header,hulls_cm=hh,hypothesis=hyp);proposal=None
 if method=='function':obj=original
 elif method=='deadline':
  proposal=evidence(original,ctx).query(query_position(own,ctx['basis']),action_radius(body)+DOMAIN_PAD)
  obj=dict(header,deadline={k:proposal[k] for k in ('status','lower_us','query_um','query_radius_um')})
 else:
  proposal=evidence(original,ctx).query(query_position(own,ctx['basis']),0)
  obj=dict(header,cone=dict(status=proposal['status'],anchor_um=proposal['query_um'],distance_lower_um=proposal.get('distance_lower_um')))
 wire=pack(obj)
 return wire,dict(original=original,source_proposal=proposal,masked_returns=int(mask.sum()),kept_xyz_sha256=hashlib.sha256(kept.tobytes()).hexdigest(),groups_cm=gg)

def decode(wire,ctx):
 obj=unpack(wire)
 if obj['kind']=='function':return BASE.decode(wire,ctx)
 assert obj['version']==1 and obj['kind'] in ('deadline','cone') and obj['context']==sha_context(ctx) and obj['blueprint'] in ctx['catalog']
 assert type(obj['source_us']) is int and obj['source_us']>=0 and type(obj['frame']) is int
 if obj['kind']=='cone':
  c=obj['cone'];assert isinstance(c['status'],str) and len(c['anchor_um'])==2 and all(type(v) is int and abs(v)<=10**9 for v in c['anchor_um'])
  assert c['distance_lower_um'] is None or type(c['distance_lower_um']) is int and 0<=c['distance_lower_um']<=10**10
  assert (c['status']=='bounded')==(c['distance_lower_um'] is not None)
  return dict(obj=obj,compiled=None)
 d=obj['deadline'];assert type(d['lower_us']) is int and 0<=d['lower_us']<=500000 and type(d['query_radius_um']) is int and 0<=d['query_radius_um']<=100000000
 assert len(d['query_um'])==2 and all(type(v) is int and abs(v)<=10**9 for v in d['query_um']) and isinstance(d['status'],str)
 obj['proposal']=dict(d,source_us=obj['source_us'],proposal_valid_until_us=obj['source_us']+d['lower_us'],family='component_mean',deployment_authorized=False,risk_certificate_applicable=False)
 return dict(obj=obj,compiled=None)


def choose(cache,own,body,ctx,now):
 if cache is None or cache['obj']['kind']!='cone':return BASE.choose(cache,own,body,ctx,now)
 obj=cache['obj'];c=obj['cone'];q=query_position(own,ctx['basis']);r=action_radius(body)
 base=dict(source_us=obj['source_us'],query_um=q,query_radius_um=r,family='component_mean',status=c['status'],deployment_authorized=False,risk_certificate_applicable=False)
 if c['status']!='bounded':proposal=dict(base,lower_us=0,proposal_valid_until_us=obj['source_us'])
 else:
  n=sum((q[k]-c['anchor_um'][k])**2 for k in (0,1));d=math.isqrt(n);d+=d*d<n;lower=max(0,c['distance_lower_um']-d);age=horizon(lower,pose.parameters(ctx['catalog'][obj['blueprint']])['body_um'],r)
  proposal=dict(base,distance_lower_um=lower,lower_us=age,proposal_valid_until_us=obj['source_us']+age,body_proofs=None,assumptions='Same center/body/motion condition; anchor lower minus outward-rounded query displacement.')
 gate=decision(proposal,now,ACTION);gate['query_domain_valid']=True
 return proposal,gate
