"""Remove redundant direct-deadline fields; preserve source age and query domain."""
import runtime as R

HEADER=('version','blueprint','source_us','frame','context')
def encode(original,proposal):
 assert proposal['source_us']==original['source_us']
 obj={k:original[k] for k in HEADER};obj['kind']='deadline'
 obj['deadline']={k:proposal[k] for k in ('status','lower_us','query_um','query_radius_um')}
 return R.pack(obj)
def decode(wire,ctx):
 obj=R.unpack(wire);assert obj['version']==1 and obj['kind']=='deadline' and obj['context']==R.sha_context(ctx) and obj['blueprint'] in ctx['catalog']
 assert type(obj['source_us']) is int and obj['source_us']>=0 and type(obj['frame']) is int
 d=obj['deadline'];assert type(d['lower_us']) is int and 0<=d['lower_us']<=500000 and type(d['query_radius_um']) is int and 0<=d['query_radius_um']<=100000000
 assert len(d['query_um'])==2 and all(type(v) is int and abs(v)<=10**9 for v in d['query_um'])
 assert isinstance(d['status'],str)
 obj['proposal']=dict(d,source_us=obj['source_us'],proposal_valid_until_us=obj['source_us']+d['lower_us'],family='component_mean',deployment_authorized=False,risk_certificate_applicable=False)
 return dict(obj=obj,compiled=None)
