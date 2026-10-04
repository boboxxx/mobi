#!/usr/bin/env python3
"""Independent raster, rational membership, integer certificates and paid replay.
Does not import producer, native library, kernel, frontend, codec, or engine.
"""
import argparse,hashlib,json,math,struct,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
PS=1000000;NS=1000000;HEADER=struct.Struct('<4sBBIIq32s32s');RAW=struct.Struct('<4sIIdI32s32s');METHODS=('active','hull','points','raw')
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def rootup(n):s=math.isqrt(n);return s+(s*s!=n)
def canonical(g):return tuple(sorted(map(tuple,g)))
def raster(xyz,T,basis,ext,static):
 local=(xyz.astype(float)@T[:3,:3].T+T[:3,3]-basis['anchor'])@np.array(basis['road']);ok=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3);v=np.floor(local*10).astype(np.int64);code=(v[:,0]+120)*161*27+(v[:,1]+80)*27+v[:,2]-3;ok&=~((local[:,2]<3)&np.isin(code,static));pp=local[ok]
 if not len(pp):return []
 ij=np.floor(pp[:,:2]/.2).astype(int);ii=ij-ij.min(0);grid=np.zeros(tuple(ii.max(0)+1),bool);grid[tuple(ii.T)]=True;labels,n=ndimage.label(grid,np.ones((3,3),int));ll=labels[tuple(ii.T)];out=[]
 for k in range(1,n+1):
  points=pp[ll==k];lo=points.min(0);hi=points.max(0)
  if len(points)>=3 and max(hi[:2]-lo[:2])<=2*math.sqrt(sum(x*x for x in ext))+.2 and hi[2]-lo[2]<=2*ext[2]+.2:out.append(np.unique(np.rint(points[:,:2]*100).astype(np.int32),axis=0).tolist())
 return out

def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def check_hull(points,vertices):
 assert vertices and len(set(map(tuple,vertices)))==len(vertices);assert set(map(tuple,vertices))<=set(map(tuple,points))
 if len(vertices)==1:assert all(p==vertices[0] for p in points)
 elif len(vertices)==2:
  a,b=vertices
  for p in points:assert cross(a,b,p)==0 and sum((p[k]-a[k])*(p[k]-b[k]) for k in (0,1))<=0
 else:
  for i,a in enumerate(vertices):
   b=vertices[(i+1)%len(vertices)];assert cross(a,b,vertices[(i+2)%len(vertices)])>0
   assert all(cross(a,b,p)>=0 for p in points)

def point_bounds(p,q,D):
 n=sum((p[k]-q[k]*D)**2 for k in (0,1));return math.isqrt(n)//D,(rootup(n)+D-1)//D

def member(p,cc,r,D):return all(sum((p[k]-c[k]*D)**2 for k in (0,1))<=(r*D)**2 for c in cc)
def dual(p,cc,w,q,r):
 tt=[[p[k]-c[k]*PS for k in (0,1)] for c in cc];u=[-sum(w[i]*tt[i][k] for i in range(len(w))) for k in (0,1)]
 if u==[0,0]:return 0
 norm=rootup(sum(t*t for t in u)*NS*NS);n=0
 for c,t,v in zip(cc,tt,w):n+=v*(sum(t[k]*(q[k]-c[k]) for k in (0,1))*NS-r*rootup(sum(x*x for x in t)*NS*NS))
 return max(0,n//norm)
def variance(cc,w,r):
 W=sum(w);s=[sum(v*c[k] for v,c in zip(w,cc)) for k in (0,1)];gap=W*sum(v*sum(t*t for t in c) for v,c in zip(w,cc))-sum(t*t for t in s)-W*W*r*r;return W,s,gap

def age(d,b):
 if d<=b:return 0
 safe=lambda t:2000000*(d-b)>10000000*t+3*t*t
 if safe(500000):return 500000
 left,right=0,500000
 while left+1<right:
  t=(left+right)//2
  if safe(t):left=t
  else:right=t
 assert safe(left) and not safe(right);return left

def verify_proof(c,vertices,allpoints,q,r):
 cc=[[t*10000 for t in p] for p in vertices];full=[[t*10000 for t in p] for p in allpoints];kind=c['kind']
 if kind=='inside':assert c['point']==[v*PS for v in q] and member(c['point'],full,r,PS);lo=hi=0
 elif kind=='dual':
  p=c['point'];ids=c['indices'];w=c['weights'];assert 1<=len(ids)<=2 and len(ids)==len(w) and all(0<=i<len(cc) for i in ids) and all(isinstance(v,int) and 0<=v<=10**12 for v in w) and sum(w)>0;assert member(p,full,r,PS);lo=dual(p,[cc[i] for i in ids],w,q,r);hi=point_bounds(p,q,PS)[1];assert hi-lo<=2
 elif kind in ('empty','singleton'):
  ids=c['indices'];w=c['weights'];assert 1<=len(ids)<=3 and len(ids)==len(w) and min(w)>=0 and sum(w)>0;W,s,gap=variance([cc[i] for i in ids],w,r);assert W==c['point_den'] and s==c['point_num'] and gap==c['variance_gap']
  if kind=='empty':assert gap>0;return None
  assert gap==0 and member(s,full,r,W);lo,hi=point_bounds(s,q,W)
 else:raise AssertionError('Uncertified '+kind)
 assert lo==c['lower_um'] and hi==c['upper_um'];return lo,hi

def active_lower(data,g,r,body):
 if data['status']!='bounded':assert data['status']==g['status'];return []
 assert len(data['queries'])==2;out=[]
 for entry,reference in zip(data['queries'],g['queries']):
  assert len(entry)==len(g['hulls_cm']);lo=[]
  for item,c,vertices in zip(entry,reference['proofs'],g['hulls_cm']):
   kind=item[0]
   if kind=='Z':assert c['kind']=='inside' and item==['Z'];lo.append(0);continue
   chosen=item[2] if kind=='D' else item[1];ids=c['indices'];expected=[[*vertices[j],w] for j,w in zip(ids,c['weights'])];assert chosen==expected;cc=[[p[0]*10000,p[1]*10000] for p in chosen];w=[p[2] for p in chosen]
   if kind=='D':assert c['kind']=='dual' and item[1]==c['point'];lo.append(dual(item[1],cc,w,reference['query'],r))
   else:
    W,s,gap=variance(cc,w,r)
    if kind=='E':assert c['kind']=='empty' and gap>0
    else:assert kind=='S' and c['kind']=='singleton' and gap==0;lo.append(point_bounds(s,reference['query'],W)[0])
  assert lo;out.append(age(min(lo),body+750000))
 return out

def independent_replay(rows,method,rate,t0,setup):
 ss=tx=rx=-10**30;jobs=[];events=[]
 if setup:
  ss=t0+setup['source_us'];tx=ss+(setup['wire_bytes']*8000000+rate-1)//rate;rx=tx+20000+setup['receiver_us'];jobs.append(dict(id='setup',source_start_us=t0,source_end_us=ss,tx_start_us=ss,tx_end_us=tx,receiver_start_us=tx+20000,arrival_us=rx,wire_bytes=setup['wire_bytes']))
 for r in sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout'])):
  m=r['methods'][method];start=max(ss,r['source_us']+r['acquisition_us']);ss=start+m['source_us'];ts=max(tx,ss);tx=ts+(m['wire_bytes']*8000000+rate-1)//rate;rs=max(rx,tx+20000);rx=rs+m['receiver_us'];d=dict(id=r['id'],source_us=r['source_us'],source_start_us=start,source_end_us=ss,tx_start_us=ts,tx_end_us=tx,receiver_start_us=rs,arrival_us=rx,wire_bytes=m['wire_bytes'],status=m['status'],deadlines_us=[r['source_us']+t for t in m['lower_us']] if m['status']=='bounded' else [-10**30]*2);jobs.append(d);events.append(d)
 out=[];i=0;dead=[(-10**30,None)]*2;revoked=False
 for step in range(16):
  now=t0+step*50000
  while i<len(events) and events[i]['arrival_us']<=now:
   e=events[i]
   if e['status']=='empty':revoked=True;dead=[(-10**30,None)]*2
   if not revoked:
    for q,d in enumerate(e['deadlines_us']):
     if d>dead[q][0]:dead[q]=(d,e['id'])
   i+=1
  for q,(d,key) in enumerate(dead):out.append(dict(step=step,query=q,now_us=now,fact_id=key,deadline_us=d,grant=not revoked and d>=now+220000))
 return dict(jobs=jobs,events=events,decisions=out,grants=sum(x['grant'] for x in out),scheduled_queries=32,wire_bytes=sum(x['wire_bytes'] for x in jobs))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');pp=ROOT/'results/prospective_expiry_20261003';pb=ROOT/'results/background_frontend_20261004';parent=read(pp/'analysis_sheng.json');ref=read(pb/'body_support_sheng.json');bg=read(pb/'background.json');rr={r['id']:r for r in parent['rows']};sg={r['id']:r['groups_cm'] for r in ref['rows']};catalog=d['context']['catalog'];basis=d['context']['basis'];assert catalog==parent['contract_body']['catalog'] and basis==parent['contract_body']['basis'];assert d['contract_sha256']==hashlib.sha256(canon(d['context'])).hexdigest() and d['calibration_sha256']==hashlib.sha256(canon(ref['registry'])).hexdigest()
 for mapping in (read(E/'freeze.json')['sources'],d['source_hashes'],d['input_hashes']):
  for name,h in mapping.items():assert sha(ROOT/name)==h,name
 b=zlib.decompress((p/'setup.bin').read_bytes());assert hashlib.sha256(b[:-32]).digest()==b[-32:] and json.loads(b[:-32])==dict(context=d['context'],background=bg);s=d['setup'];assert sha(p/'setup.bin')==s['wire_sha256'] and (p/'setup.bin').stat().st_size==s['wire_bytes']
 for dest,key in [('source_us','source_s'),('receiver_us','receiver_s')]:assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
 checks=[];certificates=points=packets=0;byep=defaultdict(list);lookup={}
 assert [r['id'] for r in d['rows']]==[r['id'] for r in parent['rows'] if r['split']=='test']
 for j,r in enumerate(d['rows']):
  old=rr[r['id']];path=pp/'capture'/old['cloud_file']
  with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform']
  groups=raster(xyz,T,basis,catalog[r['blueprint']],bg['layouts'][str(r['layout'])]['codes']);assert sorted(map(canonical,groups))==sorted(map(canonical,sg[r['id']]));groups=sg[r['id']];body=math.ceil(math.sqrt(sum(v*v for v in catalog[r['blueprint']]))*1e6);assert r['body_um']==body and r['radius_um']==body+8000+d['context']['slacks_um'][r['blueprint']];radius=r['radius_um'];g=r['geometry'];hulls=g.get('hulls_cm',[]);assert len(hulls)==len(groups)
  for full,h in zip(groups,hulls):check_hull(full,h);points+=len(full)
  bounded=g['status']=='bounded'
  if bounded:
   assert len(g['queries'])==2
   for q in g['queries']:
    bounds=[verify_proof(c,h,full,q['query'],radius) for c,h,full in zip(q['proofs'],hulls,groups)];alive=[v for v in bounds if v is not None];assert alive;lo=min(v[0] for v in alive);hi=min(v[1] for v in alive);assert q['lower_um']==lo and q['upper_um']==hi and q['lower_us']==age(lo,body+750000) and q['upper_us']==age(hi,body+750000) and hi-lo<=2 and q['upper_us']-q['lower_us']<=1;certificates+=len(bounds)
  else:
   assert g['status'] in ('refused','empty','precision_refusal')
   if g['status']=='refused':assert not groups
   # Refusal never grants from this new fact. Retaining prior facts is replayed.
   if g['status']=='empty':
    fail=g['failed_query'];assert all(verify_proof(c,h,full,fail['query'],radius) is None for c,h,full in zip(fail['proofs'],hulls,groups))
  # Exact binary float truth, used only after production; no decoder input.
  xy=old['true_xy'];fr=[v.as_integer_ratio() for v in xy];D=max(v[1] for v in fr);truth=[v[0]*(D//v[1])*1000000 for v in fr];covered=not groups or any(member(truth,[[v*10000 for v in pt] for pt in full],radius,D) for full in groups);oracle=[]
  for qx in (-6000000,6000000):
   lo,hi=point_bounds(truth,[qx,0],D);oracle.append([age(lo,body+750000),age(hi,body+750000)])
  for method,m in r['methods'].items():
   path=ROOT/m['packet'];wire=path.read_bytes();assert len(wire)==m['wire_bytes'] and sha(path)==m['wire_sha256'];b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:]
   if method=='raw':
    h=RAW.unpack(b[:RAW.size]);rc=d['context']['raw_transport'];assert h[:3]==(b'RXYZ',list(catalog).index(r['blueprint']),r['frame']) and math.floor(h[3]*1e6)==r['source_us'] and h[5].hex()==rc['contract'] and h[6].hex()==rc['calibration'];TT=np.frombuffer(b,dtype='<f8',count=16,offset=RAW.size).reshape(4,4);xx=np.frombuffer(b,dtype='<f4',count=h[4]*3,offset=RAW.size+128).reshape(-1,3);assert len(b)==RAW.size+128+h[4]*12+32;assert np.array_equal(TT,T) and np.array_equal(xx,xyz) and TT.tolist()==rc['transforms'][str(r['layout'])]
   else:
    h=HEADER.unpack(b[:HEADER.size]);assert h==(b'BEX1',METHODS.index(method),r['layout'],list(catalog).index(r['blueprint']),r['frame'],r['source_us'],bytes.fromhex(d['contract_sha256']),bytes.fromhex(d['calibration_sha256']));data=json.loads(b[HEADER.size:-32])
    if method=='active':assert active_lower(data,g,radius,body)==m['lower_us']
    elif method=='hull':assert data==hulls
    else:assert data==groups
   assert m['status']==g['status'] and m['lower_us']==([q['lower_us'] for q in g['queries']] if bounded else []);selection=max(v['selection_s'] for mm in old['methods'].values() for v in mm['samples']);assert len(m['samples'])==3 and all(v['selection_s']==selection for v in m['samples']);assert m['source_us']==math.ceil((max(v['source_s'] for v in m['samples'])+selection)*1e6) and m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);packets+=1
  check=dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],covered=covered,status=g['status'],oracle_us=oracle,expiry_us=[[q['lower_us'],q['upper_us']] for q in g['queries']] if bounded else [],distance_gap_um=[point_bounds(truth,q['query'],D)[0]-q['upper_um'] for q in g['queries']] if bounded else []);checks.append(check);byep[r['episode_id']].append(r);lookup[r['id']]=r
  if (j+1)%500==0:print('audited',j+1,flush=True)
 planned={e['episode']['id']:e for e in parent['episodes'] if e['episode']['split']=='test'};assert len(d['traces'])==len(planned)*16;seen=set();grid_checks=violations=grants=0
 for tr in d['traces']:
  key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);rows=byep[tr['episode_id']];t0=min(r['source_us'] for r in rows) if rows else 0;assert tr['t0']==t0 and tr['capture_status']==planned[tr['episode_id']]['status'];a0=independent_replay(rows,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==v for k,v in a0.items())
  for decision in tr['decisions']:
   if not decision['grant']:continue
   grants+=1;fact=lookup[decision['fact_id']];assert fact['geometry']['status']=='bounded';qx=(-6000000,6000000)[decision['query']];ep=planned[tr['episode_id']]
   for truth in ep['trajectory']:
    timestamp=math.floor(truth['timestamp']*1e6)
    if not decision['now_us']<=timestamp<=decision['now_us']+220000:continue
    position=(np.asarray(truth['center'])-basis['anchor'])@np.asarray(basis['road']);distance=math.hypot(position[0]*1e6-qx,position[1]*1e6);grid_checks+=1;violations+=int(distance<=fact['body_um']+750000)
 result=dict(frame_checks=checks,frames=len(checks),raw_packet_checks=packets,quantized_point_checks=points,intersection_certificate_checks=certificates,trace_checks=len(d['traces']),decision_checks=sum(len(t['decisions']) for t in d['traces']),grants=grants,observed_future_grid_checks=grid_checks,observed_future_grid_violations=violations,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent all-XYZ raster groups, exact hull equivalence, rational source membership, integer primal/dual bounds, actual wire fields and costs, complete three-FIFO replay. Future grid diagnostic is not intertick mesh safety. Reused data give no new risk qualification.')
 a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print('complete',len(checks),len(d['traces']),flush=True)
if __name__=='__main__':main()
