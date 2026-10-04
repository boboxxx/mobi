"""Frozen near-hazard diagnostic: same source set, fair compact scalar wire."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('near_fixed_base_runtime',Path(__file__).resolve().parents[1]/'ego_expiry_live_20261004/runtime.py')
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
for name in dir(BASE):
 if not name.startswith('__'):globals()[name]=getattr(BASE,name)

def encode(raw,T,own,body,ctx,bp,method,source_us,frame,models,background):
 wire,meta=BASE.encode(raw,T,own,body,ctx,bp,method,source_us,frame,models,background)
 if method=='deadline':
  original=meta['original'];proposal=meta['source_proposal']
  obj={k:original[k] for k in ('version','blueprint','source_us','frame','context')};obj['kind']='deadline'
  obj['deadline']={k:proposal[k] for k in ('status','lower_us','query_um','query_radius_um')}
  wire=pack(obj)
 return wire,meta

def decode(wire,ctx):
 obj=unpack(wire)
 if obj['kind']=='function':return BASE.decode(wire,ctx)
 assert obj['version']==1 and obj['kind']=='deadline' and obj['context']==sha_context(ctx) and obj['blueprint'] in ctx['catalog']
 assert type(obj['source_us']) is int and obj['source_us']>=0 and type(obj['frame']) is int
 d=obj['deadline'];assert type(d['lower_us']) is int and 0<=d['lower_us']<=500000 and type(d['query_radius_um']) is int and 0<=d['query_radius_um']<=100000000
 assert len(d['query_um'])==2 and all(type(v) is int and abs(v)<=10**9 for v in d['query_um']) and isinstance(d['status'],str)
 obj['proposal']=dict(d,source_us=obj['source_us'],proposal_valid_until_us=obj['source_us']+d['lower_us'],family='component_mean',deployment_authorized=False,risk_certificate_applicable=False)
 return dict(obj=obj,compiled=None)
