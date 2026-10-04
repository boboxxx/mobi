#!/usr/bin/env python3
"""Stored fresh chain replay with independent exact geometry and physical checks."""
import argparse,gzip,hashlib,importlib.util,json,math
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import runtime as R
E=Path(__file__).resolve().parent
def module(name,n):
 s=importlib.util.spec_from_file_location(name,R.ROOT/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=module('independent_action_geometry','experiments/action_expiry_20261004/audit.py')
B=module('independent_physical_pose','experiments/ego_actuator_realization_20261004/analyze.py')
def read(p):return json.loads(p.read_bytes())
def geometry(original,body,ctx,proposal):
 if proposal is None or proposal['status']!='bounded':return
 bp=original['blueprint'];h=original['hulls_cm'];hyp=original['hypothesis'];ext=ctx['catalog'][bp];supported=hyp.get('status')=='supported';Q=F(*ctx['registry'][bp]['supported_mean']);delta=G.up(Q*10000) if supported else int(F(*ctx['registry'][bp]['fallback_um']))
 rects=G.rectangles(h,ext,delta);assert rects
 q=proposal['query_um'];v=min(G.rect_distance(rect,q) for rect in rects);pose=math.isqrt(v.numerator//v.denominator)
 if supported:
  rr=G.up(Q*hyp['single_scale_um']);c=hyp['mean_um'];other=max(0,math.isqrt(sum((c[k]-q[k])**2 for k in (0,1)))-rr)
  assert any(G.rect_distance(rect,c)<=rr*rr for rect in rects)
 else:
  rr=G.radius(ext)+8000+delta;groups=[[[v*10000 for v in p] for p in hull] for hull in h];proofs=proposal['body_proofs'];assert len(proofs)==len(groups)
  vals=[G.body_proof(proof,group,q,rr) for proof,group in zip(proofs,groups)];other=min(v for v in vals if v is not None)
 lower=max(pose,other);assert lower==proposal['distance_lower_um'];t=proposal['lower_us'];assert 0<=t<=500000
 if t:assert G.safe(lower,G.radius(ext),proposal['query_radius_um'],t)
 if t<500000:assert not G.safe(lower,G.radius(ext),proposal['query_radius_um'],t+1)
 assert proposal['source_us']==original['source_us'] and proposal['proposal_valid_until_us']==original['source_us']+t
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 f=read(E/'freeze.json')
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert R.sha(R.ROOT/n)==h,n
 plan=read(E/'plan.json');outcomes=read(a.capture/'outcomes.json');ctx=read(a.capture/'context.json');assert [v['request'] for v in outcomes]==plan and len(plan)==12
 assert read(a.capture/'cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
 models=R.load_models();background=read(R.ROOT/'results/background_frontend_20261004/background.json');reports=[];sources_total=decisions=geometries=0;violations=dict(ego_enclosure=0,ego_speed_cap=0,self_mask_leak_returns=0,target_mask_removed_returns=0)
 for outcome in outcomes:
  path=a.capture/outcome['file'];assert R.sha(path)==outcome['sha256'];data=gzip.decompress(path.read_bytes());assert len(data)==outcome['logical_bytes'] and hashlib.sha256(data).hexdigest()==outcome['logical_sha256'];d=json.loads(data);assert d['request']==outcome['request']
  if outcome['status']!='captured':reports.append(dict(id=d['request']['id'],status=outcome['status']));continue
  rows=d['rows'];sources=d['sources'];assert len(rows)==200 and len(sources)==160;free=0;source_map={s['step']:s for s in sources};body=d['body'];request=d['request'];uncovered=0;rx=0
  for s in sources:
   cloud=a.capture/'clouds'/s['cloud'];packet=a.capture/'packets'/s['packet'];assert R.sha(cloud)==s['cloud_sha256'] and R.sha(packet)==s['packet_sha256'];wire=packet.read_bytes();assert len(wire)==s['wire_bytes']
   with np.load(cloud) as z:raw=z['raw'];T=z['transform'].copy();assert abs(float(z['timestamp'])-s['own']['timestamp'])<2e-6
   reproduced,meta=R.encode(raw,T,s['own'],body,ctx,request['blueprint'],request['method'],s['source_us'],s['frame'],models,background);assert reproduced==wire and meta==s['meta']
   xyz=np.c_[raw['x'],raw['y'],raw['z']];_,mask=R.own_mask(xyz,T,s['own'],body)
   violations['self_mask_leak_returns']+=int(((raw['id']==d['ego_id'])&~mask).sum());violations['target_mask_removed_returns']+=int(((raw['id']==d['target_id'])&mask).sum())
   arrival,free=R.source_link(s['source_us'],s['acquisition_us'],s['source_fee_us'],len(wire),request['propagation_us'],free);assert arrival==s['arrival_us'] and free==s['tx_free_us'] and s['dropped']==(30<=s['step']<50)
   if s.get('ready_us') is not None:
    assert not s['dropped'] and s['decode_at_us']>=arrival and s['ready_us']==s['decode_at_us']+R.roundup(max(1,s['receiver_fee_us']));rx+=1
   elif s['dropped']:assert s.get('receiver_fee_us',0)==0
   original=meta['original'];bp=original['blueprint'];hyp=original['hypothesis'];h=original['hulls_cm'];ext=ctx['catalog'][bp];supported=hyp.get('status')=='supported';Q=F(*ctx['registry'][bp]['supported_mean']);delta=G.up(Q*10000) if supported else int(F(*ctx['registry'][bp]['fallback_um']));rects=G.rectangles(h,ext,delta) if h else []
   truth=(np.asarray(s['truth']['center'])-ctx['basis']['anchor'])@np.asarray(ctx['basis']['road']);pt=[F.from_float(float(v))*1000000 for v in truth[:2]]
   contained=bool(rects) and any(G.inrect(rect,pt) for rect in rects)
   if supported:rr=G.up(Q*hyp['single_scale_um']);contained=contained and sum((pt[k]-hyp['mean_um'][k])**2 for k in (0,1))<=rr*rr
   else:rr=G.radius(ext)+8000+delta;contained=contained and any(G.feasible(pt,[[v*10000 for v in p] for p in hull],rr) for hull in h)
   s['_audit_contained']=bool(contained);uncovered+=not contained
   if meta['source_proposal'] is not None:geometry(original,body,ctx,meta['source_proposal']);geometries+=1
   sources_total+=1
  go=0;exclusion_go=0;transitions=[]
  for i,row in enumerate(rows):
   assert row['step']==i and row['now_us']==math.floor(row['own']['timestamp']*1000000)
   assert row['after']['frame']==row['own']['frame']+1 and abs(row['after']['timestamp']-row['own']['timestamp']-.05)<2e-6
   B.body_error(body,row['own']);B.body_error(body,row['after']);actual=row['after']['actual'];assert actual['manual_gear_shift'] and actual['gear']==1 and not actual['hand_brake'] and not actual['reverse']
   assert abs(actual['throttle']-row['requested_throttle'])<1e-6 and abs(actual['brake']-row['requested_brake'])<1e-6
   gate=row['gate'];assert not gate['deployment_authorized'];p=row['proposal'];sid=row['cache_source_step']
   if p is not None:
    s=source_map[sid];assert s['ready_us']<=row['now_us'] and not s['dropped'] and p['source_us']==s['source_us'] and not p['deployment_authorized'] and not p['risk_certificate_applicable']
    eligible=p['status']=='bounded' and p['source_us']<=row['now_us']+row['query_fee_us'] and row['now_us']+row['query_fee_us']+R.ACTION<=p['proposal_valid_until_us']
    if request['method']=='deadline':
     q=R.query_position(row['own'],ctx['basis']);n=sum((q[k]-p['query_um'][k])**2 for k in (0,1));dist=math.isqrt(n)+(math.isqrt(n)**2<n);domain=dist+R.action_radius(body)<=p['query_radius_um'];assert gate['query_domain_valid']==domain;eligible=eligible and domain
     assert p=={k:v for k,v in s['meta']['source_proposal'].items() if k!='body_proofs'}
    else:geometry(s['meta']['original'],body,ctx,p);geometries+=1
    assert gate['geometry_eligible']==eligible
   else:assert not gate['geometry_eligible'] and sid is None
   qq=R.query_position(row['own'],ctx['basis']);speed=math.hypot(*row['own']['velocity'][:2]);ok=speed<=.6 and -14000000<=qq[0]<=-6000000 and abs(qq[1])<=500000;assert ok==row['odom_ok']
   engineering=i<160 and gate['geometry_eligible'] and ok;assert engineering==row['engineering_go'];throttle,brake=R.relay(row['own'],engineering);assert throttle==row['requested_throttle'] and brake==row['requested_brake']
   violations['ego_speed_cap']+=math.hypot(*row['after']['velocity'][:2])>.75
   if engineering:
    go+=1;exclusion_go+=not source_map[sid]['_audit_contained'];radius=R.action_radius(body)
    for future in rows[i:min(i+6,len(rows))]:
     for vertex in future['after']['body_vertices']:
      xy=(np.asarray(vertex)-ctx['basis']['anchor'])@np.asarray(ctx['basis']['road']);violations['ego_enclosure']+=sum((float(xy[k])*1000000-qq[k])**2 for k in (0,1))>radius*radius
   if i and rows[i-1]['engineering_go'] and not engineering:
    end=next((j for j in range(i+1,len(rows)) if rows[j]['engineering_go']),len(rows));brakes=[dict(velocity=r['after']['velocity']) for r in rows[i:end]];index=B.stop_index(brakes)
    transitions.append(dict(step=i,interrupted=index is None and end<len(rows),first_stop_us=(index+1)*50000 if index is not None else None,confirmed_stop_us=(index+3)*50000 if index is not None else None))
   decisions+=1
  delta=np.asarray(rows[-1]['after']['center'])-rows[0]['own']['center'];progress=float(delta@np.asarray(ctx['basis']['road'])[:,0]);reports.append(dict(id=request['id'],status='captured',method=request['method'],blueprint=request['blueprint'],propagation_us=request['propagation_us'],engineering_go=go,forward_m=round(progress,6),collisions=len(d['collisions']),source_sets_not_containing_target=uncovered,engineering_go_from_uncovered_source=exclusion_go,received=rx,dropped=sum(s['dropped'] for s in sources),wire_bytes=sum(s['wire_bytes'] for s in sources),max_speed_mps=round(max(math.hypot(*r['after']['velocity'][:2]) for r in rows),6),transitions=transitions))
 result=dict(planned=12,captured=sum(v['status']=='captured' for v in reports),source_scans=sources_total,decisions=decisions,independent_geometry_queries=geometries,violations=violations,episodes=reports,freeze_sha256=R.sha(E/'freeze.json'),outcomes_sha256=R.sha(a.capture/'outcomes.json'),deployment_authorizations=0,scope='Fresh physical unqualified measured-delay ego loop, sampled diagnostics, no continuous/radio/statistical risk guarantee.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='episodes'},sort_keys=True))
if __name__=='__main__':main()
