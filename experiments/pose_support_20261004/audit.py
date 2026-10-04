#!/usr/bin/env python3
"""All-point independent yaw rectangles, rational coverage and paid FIFO replay.
Imports only the archived independent raster/hull/ball/replay auditor, never the
new observer/encoder/decoder or production kernels.
"""
import argparse,hashlib,importlib.util,json,math,struct,zlib
from collections import defaultdict
from decimal import Decimal,localcontext,ROUND_CEILING
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_body_auditor',ROOT/'experiments/body_expiry_20261004/audit.py');old_audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_audit)
HEADER=struct.Struct('<4sBBIIq32s32s');RAW=struct.Struct('<4sIIdI32s32s');PI=Decimal('3.141592653589793238462643383279502884197169399375105820974944592307816')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def up(n):k=math.isqrt(n);return k+(k*k!=n)
def radius(ext):
 with localcontext() as c:
  c.prec=80;v=sum(Decimal.from_float(float(x))**2 for x in ext).sqrt()*1000000;return int(v.to_integral_value(rounding=ROUND_CEILING))
def constants(ext,delta):
 R=radius(ext);Rxy=radius(ext[:2]);tilt=(R*87267+999999)//1000000;rot=(Rxy*8730+999999)//1000000
 with localcontext() as c:c.prec=80;xy=[int((Decimal.from_float(float(x))*1000000).to_integral_value(rounding=ROUND_CEILING)) for x in ext[:2]]
 return dict(body_um=R,xy_um=Rxy,tilt_pad_um=tilt,yaw_cell_pad_um=rot,slack_um=delta,half_extent_um=[x+tilt+rot+8000+delta for x in xy])
def verify_grid(normals):
 with localcontext() as ctx:
  ctx.prec=80
  for i,(c,s) in enumerate(normals):
   x=(Decimal(i)+Decimal('.5'))*PI/180;sn=term=x;cs=t=Decimal(1)
   for k in range(1,80):term*=-x*x/(2*k*(2*k+1));sn+=term;t*=-x*x/((2*k-1)*2*k);cs+=t
   assert abs(Decimal(c)-cs*1000000000)<1 and abs(Decimal(s)-sn*1000000000)<1
  assert PI/360+Decimal('0.000000002')<Decimal('0.00873') and 5*PI/180<Decimal('0.087267')

def all_point_ranges(groups,normals):
 axis=np.asarray(normals,dtype=np.int64);ortho=np.stack([-axis[:,1],axis[:,0]],1);out=[]
 for group in groups:
  points=np.asarray(group,dtype=np.int64)*10000;u=np.einsum('ij,kj->ik',points,axis);v=np.einsum('ij,kj->ik',points,ortho);out.append(list(zip(u.min(0).tolist(),u.max(0).tolist(),v.min(0).tolist(),v.max(0).tolist())))
 return out

def rectangles(ranges,normals,param):
 A,B=param['half_extent_um'];out=[]
 for gid,table in enumerate(ranges):
  for i,(u0,u1,v0,v1) in enumerate(table):
   c,s=normals[i];N=c*c+s*s;norm=up(N);left=u1-A*norm;right=u0+A*norm;bottom=v1-B*norm;top=v0+B*norm
   if left<=right and bottom<=top:out.append((gid,i,left,right,bottom,top,N))
 return out

def calibration_score(ranges,normals,param,xy):
 A,B=param['half_extent_um'];x,y=[Fraction.from_float(float(v))*1000000 for v in xy];values=[]
 for table in ranges:
  for i,(u0,u1,v0,v1) in enumerate(table):
   c,s=normals[i];nn=up(c*c+s*s);u=c*x+s*y;v=-s*x+c*y;excess=max(Fraction(0),u1-A*nn-u,u-u0-A*nn,v1-B*nn-v,v-v0-B*nn);values.append(math.ceil(excess/nn))
 return min(values) if values else 0

def exact_pose_geometry(rects,normals,body):
 if not rects:return None
 result=[]
 for qx in (-6000000,6000000):
  candidates=[]
  for gid,i,a,b,z,w,N in rects:
   c,s=normals[i];u=c*qx;v=-s*qx;pu=a if u<a else b if u>b else u;pv=z if v<z else w if v>w else v;n=(pu-u)*(pu-u)+(pv-v)*(pv-v);candidates.append((n,N,gid,i,a,b,z,w,pu,pv))
  best=candidates[0]
  for item in candidates[1:]:
   if item[0]*best[1]<best[0]*item[1]:best=item
  n,N,gid,i,a,b,z,w,pu,pv=best;c,s=normals[i];point=[c*pu-s*pv,s*pu+c*pv];D=N;assert a*D<=c*point[0]+s*point[1]<=b*D and z*D<=-s*point[0]+c*point[1]<=w*D
  # Verify world-coordinate rational witness independent of projected-distance units.
  assert sum((point[k]-(qx,0)[k]*D)**2 for k in (0,1))*N==n*D*D
  lo=math.isqrt(n//N);hi=lo+(lo*lo*N!=n);result.append(dict(query=[qx,0],group=gid,cell=i,bounds=[a,b,z,w],norm_sq=N,squared_num=n,squared_den=N,closest_num_um=point,closest_den=D,lower_um=lo,upper_um=hi,lower_us=old_audit.age(lo,body+750000),upper_us=old_audit.age(hi,body+750000)))
 return result

def check_sphere(g,groups,hulls,r,body):
 if not groups:assert g['status']=='refused';return []
 if g['status']=='bounded':
  out=[]
  for q in g['queries']:
   checked=[old_audit.verify_proof(c,h,gg,q['query'],r) for c,h,gg in zip(q['proofs'],hulls,groups)];alive=[v for v in checked if v is not None];assert alive;lo=min(v[0] for v in alive);hi=min(v[1] for v in alive);assert q['lower_um']==lo and q['upper_um']==hi and q['lower_us']==old_audit.age(lo,body+750000) and q['upper_us']==old_audit.age(hi,body+750000);out.append(q['lower_us'])
  return out
 assert g['status'] in ('precision_refusal','empty')
 if g['status']=='empty':
  q=g['failed_query'];assert all(old_audit.verify_proof(c,h,gg,q['query'],r) is None for c,h,gg in zip(q['proofs'],hulls,groups))
 return []

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');pp=ROOT/'results/prospective_expiry_20261003';pb=ROOT/'results/background_frontend_20261004';prior=read(pp/'analysis_sheng.json');support=read(pb/'body_support_sheng.json');bg=read(pb/'background.json');parent={r['id']:r for r in prior['rows']};reference={r['id']:r for r in support['rows']};grid=read(E/'directions.json');normals=grid['normal_xy'];assert grid['scale']==1000000000 and grid['step_degrees']==1 and len(normals)==180;ctx=d['context'];assert ctx['directions']==normals;verify_grid(normals);catalog=ctx['catalog'];basis=ctx['basis'];assert catalog==prior['contract_body']['catalog'] and basis==prior['contract_body']['basis'] and ctx['background']==bg;assert ctx['tilt_operator_norm_upper']==[87267,1000000] and ctx['yaw_cell_distance_factor']==[8730,1000000] and ctx['point_quantization_allowance_um']==8000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000) and ctx['cap_us']==500000 and ctx['query_radius_um']==750000
 frozen=read(E/'freeze.json');assert ctx['source_hashes']==d['source_hashes']==frozen['sources']
 for mapping in (d['source_hashes'],d['input_hashes'],frozen['input_hashes']):
  for n,h in mapping.items():assert sha(ROOT/n)==h,n
 assert d['contract_sha256']==hashlib.sha256(canon(ctx)).hexdigest() and d['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest();blob=zlib.decompress((p/'setup.bin').read_bytes());assert hashlib.sha256(blob[:-32]).digest()==blob[-32:] and json.loads(blob[:-32])==ctx;s=d['setup'];assert len((p/'setup.bin').read_bytes())==s['wire_bytes'] and sha(p/'setup.bin')==s['wire_sha256'];assert len(s['samples'])==3
 for dest,key in [('source_us','source_s'),('receiver_us','receiver_s')]:assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
 checks=[];scores=defaultdict(int);byep=defaultdict(list);pose_candidates=point_count=packets=0;assert [r['id'] for r in d['rows']]==[r['id'] for r in prior['rows']]
 for j,r in enumerate(d['rows']):
  old=parent[r['id']];path=pp/'capture'/old['cloud_file']
  with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform']
  ext=catalog[r['blueprint']];actual=old_audit.raster(xyz,T,basis,ext,bg['layouts'][str(r['layout'])]['codes']);groups=reference[r['id']]['groups_cm'];assert sorted(map(old_audit.canonical,actual))==sorted(map(old_audit.canonical,groups));hh=r['hulls_cm'];assert len(hh)==len(groups)
  for gg,h in zip(groups,hh):old_audit.check_hull(gg,h);point_count+=len(gg)
  ranges=all_point_ranges(groups,normals);sc=calibration_score(ranges,normals,constants(ext,0),old['true_xy']);assert sc==r['pose_score_um'] and r['body_score_um']==reference[r['id']]['score_um'] and r['joint_score_um']==max(sc,r['body_score_um']);scores[r['episode_id']]=max(scores[r['episode_id']],r['joint_score_um']);delta=d['registry'][r['blueprint']]['development_joint_slack_um'];param=constants(ext,delta);rects=rectangles(ranges,normals,param);pose_candidates+=len(rects);covered=not groups or sc<=delta
  M=np.asarray(old['sensor_transform']['matrix']);assert M.tolist()==ctx['raw_transport']['transforms'][str(r['layout'])]
  # Post-production pose prior diagnostic; not an online input or a fitted threshold.
  rotation=np.asarray(basis['road']).T@np.asarray(old['bounding_box'].get('rotation_matrix',np.eye(3)))
  episode=next(e for e in prior['episodes'] if e['episode']['id']==r['episode_id']);snap=next(v for v in episode['trajectory'] if v['frame']==r['frame']);rotation=np.asarray(basis['road']).T@np.asarray(snap['actor_transform']['matrix'])[:3,:3];yaw=math.atan2(rotation[1,0],rotation[0,0]);nominal=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1]]);operator=float(np.linalg.svd(rotation-nominal,compute_uv=False)[0]);assert old['bounding_box']['rotation']==[0.0,0.0,0.0]
  check=dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],available=bool(groups),pose_score_um=sc,joint_score_um=r['joint_score_um'],joint_covered=not groups or r['joint_score_um']<=delta,tilt_operator_norm=round(operator,12),tilt_prior_violated=operator>.087267)
  if r['split']=='test':
   assert param==r['parameters'];q=exact_pose_geometry(rects,normals,param['body_um']);status='refused' if not groups else 'empty' if not rects else 'bounded';assert r['pose_geometry']['status']==status and r['pose_geometry']['feasible_cells']==len(rects);assert r['pose_geometry']['queries']==(q or []);sphere=check_sphere(r['sphere_geometry'],groups,hh,param['body_um']+8000+delta,param['body_um']);pose=[v['lower_us'] for v in q] if q else [];sphere_status=r['sphere_geometry']['status'];joint_status='empty' if 'empty' in (status,sphere_status) else 'bounded' if pose or sphere else 'refused';joint=[max(v) for v in zip(*[v for v in (pose,sphere) if v])] if joint_status=='bounded' else [];expected={'sphere_hull':(sphere_status,sphere),'pose_hull':(status,pose),'joint_hull':(joint_status,joint),'joint_raw':(joint_status,joint)}
   for policy,m in r['methods'].items():
    assert (m['status'],m['lower_us'])==expected[policy];wire=(ROOT/m['packet']).read_bytes();assert len(wire)==m['wire_bytes'] and sha(ROOT/m['packet'])==m['wire_sha256'];b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:]
    if policy=='joint_raw':
     h=RAW.unpack(b[:RAW.size]);rc=ctx['raw_transport'];assert h[:3]==(b'RXYZ',list(catalog).index(r['blueprint']),r['frame']) and h[3]==old['timestamp'] and math.floor(h[3]*1e6)==r['source_us'] and h[5].hex()==rc['contract']==prior['contract_sha256'] and h[6].hex()==rc['calibration']==prior['calibration_sha256'];TT=np.frombuffer(b,dtype='<f8',count=16,offset=RAW.size).reshape(4,4);xx=np.frombuffer(b,dtype='<f4',count=h[4]*3,offset=RAW.size+128).reshape(-1,3);assert len(b)==RAW.size+128+h[4]*12+32 and np.array_equal(TT,T) and np.array_equal(xx,xyz)
    else:
     h=HEADER.unpack(b[:HEADER.size]);assert h==(b'BEX1',1,r['layout'],list(catalog).index(r['blueprint']),r['frame'],r['source_us'],bytes.fromhex(d['contract_sha256']),bytes.fromhex(d['calibration_sha256']));assert json.loads(b[HEADER.size:-32])==hh;assert [v['source_s'] for v in m['samples']]==r['common_hull_samples_s']
    assert len(m['samples'])==3;selection=max(v['selection_s'] for mm in old['methods'].values() for v in mm['samples']);assert all(v['selection_s']==selection for v in m['samples']);assert m['source_us']==math.ceil((max(v['source_s'] for v in m['samples'])+selection)*1e6) and m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);packets+=1
   x,y=[Fraction.from_float(float(v))*1000000 for v in old['true_xy']];oracle=[]
   for qx in (-6000000,6000000):
    dd=(x-qx)**2+y*y;lo=math.isqrt(dd.numerator//dd.denominator);hi=lo+(lo*lo*dd.denominator<dd.numerator);oracle.append([old_audit.age(lo,param['body_um']+750000),old_audit.age(hi,param['body_um']+750000)])
   check.update(oracle_us=oracle,sphere_us=sphere,pose_us=pose,joint_us=joint,pose_bracket_us=[v['upper_us']-v['lower_us'] for v in q] if q else [],pose_bracket_um=[v['upper_um']-v['lower_um'] for v in q] if q else []);byep[r['episode_id']].append(r)
  checks.append(check)
  if (j+1)%500==0:print('audited',j+1,flush=True)
 for ep in prior['episodes']:scores.setdefault(ep['episode']['id'],0)
 for bp in catalog:
  ss=[scores[e['episode']['id']] for e in prior['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ss)==95 and max(ss)==d['registry'][bp]['development_joint_slack_um']==ctx['slacks_um'][bp]
 # Producer omits wholly failed episodes from its score mapping by design; values default zero.
 assert all(scores[k]==v for k,v in d['joint_episode_scores'].items())
 planned={e['episode']['id']:e for e in prior['episodes'] if e['episode']['split']=='test'};assert len(d['traces'])==len(planned)*16;seen=set();grid_checks=violations=grants=0;lookup={r['id']:r for r in d['rows']}
 for tr in d['traces']:
  key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['t0']==t0 and tr['capture_status']==planned[tr['episode_id']]['status'];expected=old_audit.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==v for k,v in expected.items())
  for decision in tr['decisions']:
   if not decision['grant']:continue
   grants+=1;fact=lookup[decision['fact_id']];qx=(-6000000,6000000)[decision['query']]
   for truth in planned[tr['episode_id']]['trajectory']:
    stamp=math.floor(truth['timestamp']*1e6)
    if decision['now_us']<=stamp<=decision['now_us']+220000:
     position=(np.asarray(truth['center'])-basis['anchor'])@np.asarray(basis['road']);grid_checks+=1;violations+=int(math.hypot(position[0]*1e6-qx,position[1]*1e6)<=fact['parameters']['body_um']+750000)
 out=dict(frame_checks=checks,frames=len(checks),complete_pose_rectangle_checks=pose_candidates,quantized_point_checks=point_count,actual_packet_checks=packets,trace_checks=len(d['traces']),decision_checks=sum(len(t['decisions']) for t in d['traces']),grants=grants,observed_future_grid_checks=grid_checks,observed_future_grid_violations=violations,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='All raw XYZ raster groups and all-point directional ranges, complete yaw family, rational calibration, exact distance witnesses, real packet fields/maxima and independently reconstructed three-FIFO policies. Tilt is observed diagnostic; reused-data coverage is not prospective risk qualification or unknown-inventory/continuous mesh safety.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('complete',len(checks),len(d['traces']),flush=True)
if __name__=='__main__':main()
