"""Four actual wire formats preserving the same source-body support model."""
import hashlib,json,struct,zlib
import numpy as np
from frontend import groups
from kernel import geometry,dual_lower,point_distance,horizon
HEADER=struct.Struct('<4sBBIIq32s32s')
METHODS=('active','hull','points','raw')
RAW_HEADER=struct.Struct('<4sIIdI32s32s')
def pack_raw(xyz,T,ci,frame,stamp,contract,calibration):
 a=np.asarray(xyz,dtype='<f4');blob=RAW_HEADER.pack(b'RXYZ',ci,frame,stamp,len(a),bytes.fromhex(contract),bytes.fromhex(calibration))+np.asarray(T,dtype='<f8').tobytes()+a.tobytes();return zlib.compress(blob+hashlib.sha256(blob).digest(),6)
def pack(method,data,ci,layout,frame,source,contract,calibration):
 assert method!='raw'
 head=HEADER.pack(b'BEX1',METHODS.index(method),layout,ci,frame,source,bytes.fromhex(contract),bytes.fromhex(calibration));payload=json.dumps(data,separators=(',',':')).encode();body=head+payload;return zlib.compress(body+hashlib.sha256(body).digest(),6)

def active_data(g):
 if g['status']!='bounded':return dict(status=g['status'],queries=[])
 out=[]
 for query in g['queries']:
  proofs=[]
  for i,c in enumerate(query['proofs']):
   centers=g['hulls_cm'][i]
   if c['kind']=='inside':proofs.append(['Z'])
   elif c['kind']=='dual':proofs.append(['D',c['point'],[[*centers[j],w] for j,w in zip(c['indices'],c['weights'])]])
   else:proofs.append(['E' if c['kind']=='empty' else 'S',[[*centers[j],w] for j,w in zip(c['indices'],c['weights'])]])
  out.append(proofs)
 return dict(status='bounded',queries=out)

def check_active(d,r,body):
 if d['status']!='bounded':return dict(status=d['status'],lower_us=[])
 assert len(d['queries'])==2;out=[]
 for q,proofs in zip(((-6000000,0),(6000000,0)),d['queries']):
  assert proofs;lo=[]
  for proof in proofs:
   kind=proof[0]
   if kind=='Z':lo.append(0);continue
   selected=proof[2] if kind=='D' else proof[1];assert 1<=len(selected)<=3 and all(isinstance(v,int) for row in selected for v in row);cc=[[p[0]*10000,p[1]*10000] for p in selected];w=[p[2] for p in selected];assert min(w)>=0 and sum(w)>0
   if kind=='D':
    assert len(w)<=2 and max(w)<=10**12 and len(proof[1])==2;lo.append(dual_lower(proof[1],cc,list(range(len(cc))),w,q,r))
   else:
    assert kind in ('E','S');W=sum(w);s=[sum(w[i]*cc[i][k] for i in range(len(w))) for k in (0,1)];gap=W*sum(w[i]*sum(x*x for x in cc[i]) for i in range(len(w)))-sum(x*x for x in s)-W*W*r*r
    if kind=='E':assert gap>0
    else:assert gap==0;lo.append(point_distance(s,q,W)[0])
  if not lo:return dict(status='empty',lower_us=[])
  out.append(horizon(min(lo),body+750000))
 return dict(status='bounded',lower_us=out)

def unpack(wire,expected,contract,calibration,catalog,bg,basis,slacks,raw_context=None):
 blob=zlib.decompress(wire);assert hashlib.sha256(blob[:-32]).digest()==blob[-32:]
 if expected=='raw':
  assert raw_context;h=RAW_HEADER.unpack(blob[:RAW_HEADER.size]);assert h[0]==b'RXYZ' and h[5].hex()==raw_context['contract'] and h[6].hex()==raw_context['calibration'];ci,frame,source=h[1],h[2],__import__('math').floor(h[3]*1e6);assert 0<=ci<len(catalog);T=np.frombuffer(blob,dtype='<f8',count=16,offset=RAW_HEADER.size).reshape(4,4);assert len(blob)==RAW_HEADER.size+128+h[4]*12+32;xyz=np.frombuffer(blob,dtype='<f4',count=h[4]*3,offset=RAW_HEADER.size+128).reshape(-1,3);matches=[int(k) for k,v in raw_context['transforms'].items() if np.array_equal(T,v)];assert len(matches)==1;layout=matches[0];bp=list(catalog)[ci];extent=catalog[bp];body=__import__('math').ceil(__import__('math').sqrt(sum(v*v for v in extent))*1e6);gg=groups(xyz,T,np.asarray(basis['anchor']),np.asarray(basis['road']),extent,bg['layouts'][str(layout)]['codes']);g=geometry(gg,body+8000+slacks[bp],body);return dict(status=g['status'],lower_us=[q['lower_us'] for q in g['queries']] if g['status']=='bounded' else [],class_index=ci,layout=layout,frame=frame,source_us=source)
 h=HEADER.unpack(blob[:HEADER.size]);assert h[0]==b'BEX1' and h[1]==METHODS.index(expected) and h[6].hex()==contract and h[7].hex()==calibration;ci,layout,frame,source=h[3],h[2],h[4],h[5];assert 0<=ci<len(catalog) and layout in (0,1);bp=list(catalog)[ci];extent=catalog[bp];body=__import__('math').ceil(__import__('math').sqrt(sum(v*v for v in extent))*1e6);r=body+8000+slacks[bp];data=blob[HEADER.size:-32]
 if expected=='active':result=check_active(json.loads(data),r,body)
 else:
  gg=json.loads(data)
  g=geometry(gg,r,body);result=dict(status=g['status'],lower_us=[q['lower_us'] for q in g['queries']] if g['status']=='bounded' else [])
 return dict(**result,class_index=ci,layout=layout,frame=frame,source_us=source)
