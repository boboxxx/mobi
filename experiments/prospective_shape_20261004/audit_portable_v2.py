#!/usr/bin/env python3
"""Independent portable audit v2: exact affine error check for stored projected truth; unchanged exact membership, geometry, calibration, wires and FIFOs."""
import argparse,hashlib,importlib.util,json,math,struct,zlib
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_pose',ROOT/'experiments/pose_support_20261004/audit.py');ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
HEADER=struct.Struct('<4sBBIIq32s32s');RAW=struct.Struct('<4sIIdI32s32s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def body_score(gg,base,xy):
 c=[F.from_float(float(v))*1000000 for v in xy];out=[]
 for g in gg:
  distances=[]
  for pt in g:
   n=sum((pt[k]*10000-c[k])**2 for k in (0,1));lo=math.isqrt(n.numerator//n.denominator);distances.append(lo+(lo*lo*n.denominator<n.numerator))
  out.append(max(0,max(distances)-base))
 return min(out) if out else 0
def affine_error(center,basis,stored):
 # Eight basic correctly-rounded binary64 operations suffice for a 3D affine
 # coordinate. 16*u times input-product magnitude dominates gamma_8, including
 # subtraction error. Exact fractions check the residual, not a fitted epsilon.
 maximum=F(0);u=F(1,2**53)
 for k in (0,1):
  terms=[(F.from_float(float(center[i]))-F.from_float(float(basis['anchor'][i])))*F.from_float(float(basis['road'][i][k])) for i in range(3)];exact=sum(terms,F(0));magnitude=sum((abs(F.from_float(float(center[i])))+abs(F.from_float(float(basis['anchor'][i]))))*abs(F.from_float(float(basis['road'][i][k]))) for i in range(3));bound=16*u*magnitude;error=abs(F.from_float(float(stored[k]))-exact);assert error<=bound and bound<F(1,10**9);maximum=max(maximum,error)
 return maximum
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');records=read(p/'capture/record.json');eps=read(p/'capture/episodes.json');manifest=read(p/'capture/manifest.json');plan=read(E/'plan.json');catalog=read(E/'catalog.json');f=read(E/'freeze.json');ctx=d['context'];basis=ctx['basis'];bg=read(ROOT/'results/background_frontend_20261004/background.json');receipt=read(p/'calibration_frozen.json');normals=ctx['directions'];ind.verify_grid(normals);assert ctx['background']==bg and ctx['catalog']==catalog and ctx['source_hashes']==d['source_hashes']==f['sources']
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 assert len(normals)==180 and normals==read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'] and basis==bg['basis']
 for n,h in d['input_hashes'].items():assert sha(ROOT/n)==h,n
 assert ctx['tilt_operator_norm_upper']==[87267,1000000] and ctx['yaw_cell_distance_factor']==[8730,1000000] and ctx['point_quantization_allowance_um']==8000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000) and ctx['query_radius_um']==750000 and ctx['cap_us']==500000
 for name,key in [('capture.py','source_sha256'),('plan.json','plan_sha256'),('PROTOCOL.md','protocol_sha256')]:assert sha(E/name)==manifest[key]
 assert len(eps)==len(plan)==930 and [e['episode'] for e in eps]==plan and [r['id'] for r in d['rows']]==[r['id'] for r in records];assert all('Town10HD_Opt' in e['map'] for e in eps if e['status']=='captured')
 for ci,bp in enumerate(catalog):
  for split,n,seed in [('calibration',95,2026103100+ci),('test',60,2026103200+ci)]:
   rng=np.random.RandomState(seed);items=[e for e in plan if e['blueprint']==bp and e['split']==split];assert len(items)==n
   for i,e in enumerate(items):
    vals=[float(rng.uniform(-8,8)),float(rng.uniform(-4,4)),float(rng.uniform(0,360)),float(rng.uniform(.5,1.8) if bp.startswith('walker.') else rng.uniform(1,3))];actual=[e[k] for k in ['longitudinal_m','lateral_m','yaw_deg','target_speed_mps']];assert e['index']==i and e['seed']==seed and actual[:3]==vals[:3];assert actual[3]==vals[3] or (bp.startswith('walker.') and abs(F.from_float(actual[3])-F.from_float(vals[3]))<=F.from_float(float(np.spacing(max(abs(actual[3]),abs(vals[3]))))))
 assert d['capture_manifest_sha256']==sha(p/'capture/manifest.json') and d['episodes']==eps;assert receipt['registry']==d['registry'] and receipt['source_hashes']==f['sources'] and d['calibration_receipt_sha256']==ctx['calibration_receipt_sha256']==sha(p/'calibration_frozen.json')
 record_splits={str((p/'capture'/r['cloud_file']).relative_to(ROOT)):r['split'] for r in records};assert len(record_splits)==len(records)
 for n,h in receipt['input_hashes'].items():assert sha(ROOT/n)==h and record_splits[n]=='calibration'
 assert d['calibration_sha256']==receipt['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest() and d['contract_sha256']==hashlib.sha256(canon(ctx)).hexdigest();rc=ctx['raw_transport'];assert rc['contract']==hashlib.sha256(canon(ctx['raw_transport_body'])).hexdigest() and rc['calibration']==d['calibration_sha256'];transport=ctx['raw_transport_body'];assert transport==dict(experiment=E.name,catalog=catalog,basis=basis,transforms=rc['transforms'],source_hashes=f['sources'])
 blob=zlib.decompress((p/'setup.bin').read_bytes());assert hashlib.sha256(blob[:-32]).digest()==blob[-32:] and json.loads(blob[:-32])==ctx;s=d['setup'];assert len((p/'setup.bin').read_bytes())==s['wire_bytes'] and sha(p/'setup.bin')==s['wire_sha256'] and len(s['samples'])==3
 for dest,key in [('source_us','source_s'),('receiver_us','receiver_s')]:assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
 source={r['id']:r for r in records};episode={e['episode']['id']:e for e in eps};checks=[];scores=defaultdict(int);byep=defaultdict(list);point_count=rect_count=packet_count=0;coordinate_error=F(0)
 for j,r in enumerate(d['rows']):
  old=source[r['id']];path=p/'capture'/old['cloud_file'];assert sha(path)==old['cloud_sha256'];assert all(r[k]==v for k,v in old.items());assert old['selection_s']>0 and old['points']==math.ceil(old['original_points']/4)
  with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform'];assert float(z['timestamp'])==old['timestamp']
  ext=catalog[r['blueprint']];assert old['bounding_box']['extent']==ext and old['bounding_box']['rotation']==[0.0,0.0,0.0] and old['sensor_frame']==old['frame'];assert T.tolist()==old['sensor_transform']['matrix']==rc['transforms'][str(r['layout'])];coordinate_error=max(coordinate_error,affine_error(old['center'],basis,r['true_xy']));assert r['source_us']==math.floor(old['timestamp']*1e6) and r['acquisition_us']==math.ceil(old['acquisition_s']*1e6)
  gg=r['groups_cm'];actual=ind.old_audit.raster(xyz,T,basis,ext,bg['layouts'][str(r['layout'])]['codes']);assert sorted(map(ind.old_audit.canonical,actual))==sorted(map(ind.old_audit.canonical,gg));hh=r['hulls_cm'];assert len(hh)==len(gg) and r['available']==bool(gg)
  for group,h in zip(gg,hh):ind.old_audit.check_hull(group,h);point_count+=len(group)
  ranges=ind.all_point_ranges(gg,normals);sc=ind.calibration_score(ranges,normals,ind.constants(ext,0),r['true_xy']);bs=body_score(gg,ind.radius(ext)+8000,r['true_xy']);assert (sc,bs,max(sc,bs))==(r['pose_score_um'],r['body_score_um'],r['joint_score_um']);scores[r['episode_id']]=max(scores[r['episode_id']],max(sc,bs));delta=d['registry'][r['blueprint']]['joint_slack_um'];param=ind.constants(ext,delta);rects=ind.rectangles(ranges,normals,param);rect_count+=len(rects);snap=next(v for v in episode[r['episode_id']]['trajectory'] if v['frame']==r['frame']);rotation=np.asarray(basis['road']).T@np.asarray(snap['actor_transform']['matrix'])[:3,:3];vertical=float(np.linalg.norm(rotation[:,2]-[0,0,1]));check=dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],available=bool(gg),pose_score_um=sc,body_score_um=bs,joint_score_um=max(sc,bs),joint_covered=not gg or max(sc,bs)<=delta,vertical_tilt_lower_bound=round(vertical,10),tilt_prior_violated=vertical>.087267)
  if r['split']=='test':
   assert param==r['parameters'];q=ind.exact_pose_geometry(rects,normals,param['body_um']);status='refused' if not gg else 'empty' if not rects else 'bounded';assert r['pose_geometry']==dict(status=status,queries=q or [],feasible_cells=len(rects));sphere=ind.check_sphere(r['sphere_geometry'],gg,hh,param['body_um']+8000+delta,param['body_um']);pose=[v['lower_us'] for v in q] if q else [];ss=r['sphere_geometry']['status'];js='empty' if 'empty' in (status,ss) else 'bounded' if pose or sphere else 'refused';joint=[max(v) for v in zip(*[v for v in (pose,sphere) if v])] if js=='bounded' else [];expected={'sphere_hull':(ss,sphere),'pose_hull':(status,pose),'joint_hull':(js,joint),'joint_raw':(js,joint)}
   for policy,m in r['methods'].items():
    assert (m['status'],m['lower_us'])==expected[policy];wire=(ROOT/m['packet']).read_bytes();assert len(wire)==m['wire_bytes'] and sha(ROOT/m['packet'])==m['wire_sha256'];b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:]
    if policy=='joint_raw':
     h=RAW.unpack(b[:RAW.size]);assert h[:3]==(b'RXYZ',list(catalog).index(r['blueprint']),r['frame']) and h[3]==r['timestamp'] and h[5].hex()==rc['contract'] and h[6].hex()==d['calibration_sha256'];TT=np.frombuffer(b,dtype='<f8',count=16,offset=RAW.size).reshape(4,4);xx=np.frombuffer(b,dtype='<f4',count=h[4]*3,offset=RAW.size+128).reshape(-1,3);assert len(b)==RAW.size+128+h[4]*12+32 and np.array_equal(TT,T) and np.array_equal(xx,xyz)
    else:
     h=HEADER.unpack(b[:HEADER.size]);assert h==(b'BEX1',1,r['layout'],list(catalog).index(r['blueprint']),r['frame'],r['source_us'],bytes.fromhex(d['contract_sha256']),bytes.fromhex(d['calibration_sha256']));assert json.loads(b[HEADER.size:-32])==hh and [v['source_s'] for v in m['samples']]==r['common_hull_samples_s']
    assert len(m['samples'])==3 and all(v['selection_s']==r['selection_s'] for v in m['samples']);assert m['source_us']==math.ceil((max(v['source_s'] for v in m['samples'])+r['selection_s'])*1e6) and m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);packet_count+=1
   x,y=[F.from_float(float(v))*1000000 for v in r['true_xy']];oracle=[]
   for qx in (-6000000,6000000):
    n=(x-qx)**2+y*y;lo=math.isqrt(n.numerator//n.denominator);hi=lo+(lo*lo*n.denominator<n.numerator);oracle.append([ind.old_audit.age(lo,param['body_um']+750000),ind.old_audit.age(hi,param['body_um']+750000)])
   check.update(sphere_us=sphere,pose_us=pose,joint_us=joint,oracle_us=oracle,pose_bracket_um=[v['upper_um']-v['lower_um'] for v in q] if q else [],pose_bracket_us=[v['upper_us']-v['lower_us'] for v in q] if q else []);byep[r['episode_id']].append(r)
  checks.append(check)
  if (j+1)%500==0:print('audited',j+1,flush=True)
 for e in plan:scores.setdefault(e['id'],0)
 assert dict(scores)==d['joint_episode_scores'] and receipt['calibration_episode_scores']=={e['id']:scores[e['id']] for e in plan if e['split']=='calibration'}
 for bp in catalog:
  values=[scores[e['id']] for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(values)==95;assert d['registry'][bp]==dict(joint_slack_um=max(values),calibration_n=95,rank=95,episode_failure_target=.05,calibration_failure_bound=.95**95) and max(values)==ctx['slacks_um'][bp]
 assert d['joint_calibration_confidence_lower']==1-6*.95**95 and len(d['traces'])==5760;seen=set();grants=grid=conflicts=0;lookup={r['id']:r for r in d['rows']}
 for tr in d['traces']:
  key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['t0']==t0 and tr['capture_status']==episode[tr['episode_id']]['status'];v=ind.old_audit.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==value for k,value in v.items())
  for dec in tr['decisions']:
   if not dec['grant']:continue
   grants+=1;fact=lookup[dec['fact_id']];qx=(-6000000,6000000)[dec['query']]
   for snap in episode[tr['episode_id']]['trajectory']:
    stamp=math.floor(snap['timestamp']*1e6)
    if dec['now_us']<=stamp<=dec['now_us']+220000:
     xy=(np.asarray(snap['center'])-basis['anchor'])@np.asarray(basis['road']);grid+=1;conflicts+=int(math.hypot(xy[0]*1e6-qx,xy[1]*1e6)<=fact['parameters']['body_um']+750000)
 physical=[]
 for bp,ext in catalog.items():
  corners=outside=motion=motion_bad=0;max_excess=0.;R=ind.radius(ext)/1e6
  for ep in eps:
   if ep['status']!='captured' or ep['episode']['blueprint']!=bp:continue
   assert ep['bounding_box']['extent']==ext
   for t in ep['trajectory']:
    for v in t['world_vertices']:corners+=1;outside+=math.hypot(v[0]-t['center'][0],v[1]-t['center'][1])>R
   for r in [v for v in d['rows'] if v['episode_id']==ep['episode']['id']]:
    for t in ep['trajectory']:
     dt=t['timestamp']-r['timestamp']
     if not 0<=dt<=.500001:continue
     displacement=math.hypot(t['center'][0]-r['center'][0],t['center'][1]-r['center'][1]);limit=5*dt+1.5*dt*dt;motion+=1;motion_bad+=displacement>limit+0.000008;max_excess=max(max_excess,displacement-limit)
  physical.append(dict(blueprint=bp,xy_corner_checks=corners,xy_outside_corners=outside,source_future_displacement_checks=motion,source_future_displacement_violations=motion_bad,max_positive_displacement_excess_um_ceil=math.ceil(max(0,max_excess)*1e6),diagnostic_precision_allowance_um=8))
 cleanup=read(p/'capture/cleanup.json');assert cleanup['vehicles']==cleanup['walkers']==cleanup['sensors']==0 and not cleanup['synchronous']
 out=dict(coordinate_rounding_checks=len(checks),maximum_affine_error_um=dict(numerator=(coordinate_error*1000000).numerator,denominator=(coordinate_error*1000000).denominator),frame_checks=checks,frames=len(checks),complete_pose_rectangle_checks=rect_count,quantized_point_checks=point_count,actual_packet_checks=packet_count,trace_checks=len(d['traces']),decision_checks=len(d['traces'])*32,grants=grants,observed_future_grid_checks=grid,observed_future_grid_violations=conflicts,physical_snapshot_checks=physical,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),calibration_receipt_sha256=sha(p/'calibration_frozen.json'),scope='Independent plan/freeze/raw raster/all-point geometry/membership/calibration/actual wires/fees/three FIFO replay, plus offline physical snapshots. Fresh law is assumed iid whole episodes; no conditional-grant risk, unknown inventory, continuous physics or ego novelty.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('complete',len(checks),len(d['traces']),flush=True)
if __name__=='__main__':main()
