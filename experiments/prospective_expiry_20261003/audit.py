#!/usr/bin/env python3
"""Independent raw components, order statistic, wire, time and causal queues."""
import argparse,hashlib,importlib.util,json,math,struct,sys,zlib
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_positive_audit',ROOT/'experiments/positive_state_20261003/audit.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
PH=struct.Struct('<4sHHIIdI32s32s');OH=struct.Struct('<4sIIdI32s32s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def qtime(t):return math.floor(t*1e6)
def read(p):return json.loads(p.read_bytes())
def queues(rows,method,rate,t0):
    # Calendar job releases at each stage, independently ordered rather than
    # importing the producer's combined recurrence or replay implementation.
    source_jobs=sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout']));source_done=[];busy=-10**30
    for r in source_jobs:
        start=max(busy,r['source_us']+r['acquisition_us']);end=start+r['methods'][method]['source_us'];busy=end;source_done.append((r,start,end))
    transmissions=[];busy=-10**30
    for r,ss,se in sorted(source_done,key=lambda x:x[2]):
        ts=max(busy,se);te=ts+(r['methods'][method]['wire_bytes']*8000000+rate-1)//rate;busy=te;transmissions.append((r,ss,se,ts,te))
    events=[];busy=-10**30
    for r,ss,se,ts,te in sorted(transmissions,key=lambda x:x[4]+20000):
        rs=max(busy,te+20000);re=rs+r['methods'][method]['receiver_us'];busy=re
        life=[min(200000,b['lower_us']) if method=='fixed200' else b['lower_us'] for b in r['bounds']]
        events.append(dict(id=r['id'],source_us=r['source_us'],source_start_us=ss,source_end_us=se,tx_start_us=ts,tx_end_us=te,receiver_start_us=rs,arrival_us=re,wire_bytes=r['methods'][method]['wire_bytes'],deadlines_us=[r['source_us']+h if r['available'] else -10**30 for h in life]))
    decisions=[]
    for step in range(16):
        now=t0+step*50000;delivered=[e for e in events if e['arrival_us']<=now]
        for q in range(2):
            eligible=[(e['deadlines_us'][q],i,e['id']) for i,e in enumerate(delivered) if e['deadlines_us'][q]>-10**30]
            best=max(eligible,key=lambda x:(x[0],-x[1])) if eligible else (-10**30,0,None)
            decisions.append(dict(step=step,query=q,now_us=now,fact_id=best[2],deadline_us=best[0],grant=best[0]>=now+220000))
    return dict(events=events,decisions=decisions,wire_bytes=sum(e['wire_bytes'] for e in events),grants=sum(d['grant'] for d in decisions),scheduled_queries=32)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');plan=read(HERE/'plan.json');eps=read(p/'capture/episodes.json');records=read(p/'capture/record.json');manifest=read(p/'capture/manifest.json');catalog=read(HERE/'catalog.json');bps=list(catalog)
    for hashes in (read(HERE/'capture_freeze.json')['source_hashes'],d['source_hashes'],d['input_hashes']):
        for name,h in hashes.items():
            target=HERE/'audit_at_evaluation.py' if name=='experiments/causal_state_20261003/audit.py' else ROOT/name
            assert sha(target)==h,name
    assert d['capture_manifest_sha256']==sha(p/'capture/manifest.json')
    for name,key in [('capture.py','source_sha256'),('plan.json','plan_sha256'),('PROTOCOL.md','protocol_sha256')]:assert sha(HERE/name)==manifest[key]
    assert len(plan)==len(eps)==930 and [e['episode'] for e in eps]==plan
    for ci,bp in enumerate(bps):
        for split,n,seed in [('calibration',95,2026102100+ci),('test',60,2026102200+ci)]:
            rng=np.random.RandomState(seed);items=[e for e in plan if e['blueprint']==bp and e['split']==split];assert len(items)==n
            for ep in items:
                vals=[float(rng.uniform(-8,8)),float(rng.uniform(-4,4)),float(rng.uniform(0,360)),float(rng.uniform(.5,1.8) if bp.startswith('walker.') else rng.uniform(1,3))]
                expected=[ep[k] for k in ('longitudinal_m','lateral_m','yaw_deg','target_speed_mps')]
                assert all(abs(x-y)<=2*abs(float(np.spacing(y))) for x,y in zip(vals,expected))
    byep={e['episode']['id']:e for e in eps};score={e['episode']['id']:0. for e in eps};original={r['id']:r for r in d['rows']};checks={};stored=reported=packets=ages=0
    for r in records:
        ep=byep[r['episode_id']];assert ep['status']=='captured' and ep['actor_id']==r['actor_id'];truth=ep['trajectory'][r['step']]
        assert r['frame']==r['sensor_frame']==truth['frame'] and r['timestamp']==r['snapshot_timestamp']==truth['timestamp'] and r['center']==truth['center']
        path=p/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
        with np.load(path) as z:raw=z['raw'];matrix=z['transform'];assert float(z['timestamp'])==r['timestamp'];np.testing.assert_array_equal(matrix,r['sensor_transform']['matrix'])
        assert len(raw)==r['points']==(r['original_points']+3)//4 and r['sampling_stride']==4
        assert int(np.sum(raw['id']==r['actor_id']))==r['actor_returns'];stored+=len(raw);reported+=r['original_points']
        anchor=np.r_[r['query'],0.];yaw=math.radians(r['road_yaw']);road=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1.]])
        c,_=old.proposals(raw,matrix,anchor,yaw,catalog[r['blueprint']]);cm=np.rint(c*100).astype(np.int32);true=(np.array(r['center'])-anchor)@road;available=bool(len(c));residual=min(math.hypot(*(t-true[:2])) for t in c) if available else 0.;score[r['episode_id']]=max(score[r['episode_id']],residual)
        fr=original[r['id']];np.testing.assert_array_equal(cm,np.asarray(fr['centers_cm'],dtype=np.int32).reshape(-1,2));assert fr['available']==available and abs(fr['residual_m']-residual)<1e-10;np.testing.assert_allclose(fr['true_xy'],true[:2],atol=1e-12,rtol=0)
        checks[r['id']]=dict(centers=c,cm=cm,true=true[:2],available=available,raw=raw,transform=matrix,source=r)
    registry={}
    for bp in bps:
        cal=[score[e['id']] for e in plan if e['blueprint']==bp and e['split']=='calibration'];radius=math.ceil(max(cal)*1e6+1e-7)+8000;registry[bp]=dict(radius_um=radius,calibration_n=95,rank=95,episode_failure_target=.05,calibration_failure_bound=.95**95)
    assert registry==d['registry'];cal=hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest();contract=hashlib.sha256(json.dumps(d['contract_body'],sort_keys=True).encode()).hexdigest();assert cal==d['calibration_sha256'] and contract==d['contract_sha256'];assert d['contract_body']['catalog']==catalog
    for fr in d['rows']:
        f=checks[fr['id']];r=f['source'];bp=r['blueprint'];radius=registry[bp]['radius_um'];covered=not f['available'] or min(math.hypot(*(c/100.-f['true'])) for c in f['cm'])*1e6<=radius;assert fr['covered']==covered
        assert fr['source_us']==qtime(r['timestamp']) and fr['acquisition_us']==math.ceil(r['acquisition_s']*1e6)
        for j,qx in enumerate((-6000000,6000000)):
            lo,up=old.horizon(f['cm'],radius,catalog[bp],qx) if f['available'] else (0,500000);b=fr['bounds'][j];assert (lo,up)==(b['lower_us'],b['upper_us']);ages+=1
        for method in ('union','lossless_centers','full_xyz'):
            m=fr['methods'][method];wire=(p/m['packet']).read_bytes();assert len(wire)==m['wire_bytes'] and sha(p/m['packet'])==m['wire_sha256']
            assert len(m['samples'])==3 and all(min(s.values())>=0 and all(math.isfinite(v) for v in s.values()) for s in m['samples'])
            assert m['source_us']==math.ceil(max(s['source_s'] for s in m['samples'])*1e6) and m['receiver_us']==math.ceil(max(s['receiver_s'] for s in m['samples'])*1e6)
            if method=='union':
                h=PH.unpack(wire[:PH.size]);n=struct.unpack('<I',wire[PH.size:PH.size+4])[0];assert h[:2]==(b'PCS1',1) and h[2]==int(not f['available']) and h[3]==bps.index(bp) and h[4]==r['frame'] and h[5]==r['timestamp'] and h[7].hex()==contract and h[8].hex()==cal
                assert hashlib.sha256(wire[:-32]).digest()==wire[-32:] and len(wire)==PH.size+4+8*n+32
                ccm=np.frombuffer(wire,dtype='<i4',count=n*2,offset=PH.size+4).reshape(-1,2);assert h[6]==(radius if f['available'] else 0)
                if f['available']:np.testing.assert_array_equal(ccm,f['cm'])
                else:assert n==0
            else:
                blob=zlib.decompress(wire);assert hashlib.sha256(blob[:-32]).digest()==blob[-32:];h=OH.unpack(blob[:OH.size]);assert h[0]==(b'RXYZ' if method=='full_xyz' else b'LCEN') and h[1]==bps.index(bp) and h[2]==r['frame'] and h[3]==r['timestamp'] and h[5].hex()==contract and h[6].hex()==cal;offset=OH.size
                if method=='full_xyz':
                    matrix=np.frombuffer(blob,dtype='<f8',count=16,offset=offset).reshape(4,4);offset+=128;np.testing.assert_array_equal(matrix,f['transform']);xyz=np.frombuffer(blob,dtype='<f4',count=h[4]*3,offset=offset).reshape(-1,3)
                    np.testing.assert_array_equal(xyz,np.c_[f['raw']['x'],f['raw']['y'],f['raw']['z']]);assert len(blob)==offset+len(xyz)*12+32
                else:
                    c=np.frombuffer(blob,dtype='<f8',count=h[4]*2,offset=offset).reshape(-1,2);assert len(blob)==offset+len(c)*16+32;np.testing.assert_array_equal(np.rint(c*100).astype(np.int32),f['cm']);np.testing.assert_allclose(c,f['centers'],atol=1e-10,rtol=0)
            packets+=1
    summary=[];motion_checks=motion_failures=body_failures=0;max_body_excess=0.
    for ep in eps:
        if ep['status']!='captured':continue
        tr=ep['trajectory'];assert len(tr)==21 and [x['step'] for x in tr]==list(range(21));bp=ep['episode']['blueprint'];body=math.ceil(math.sqrt(sum(x*x for x in catalog[bp]))*1e6)/1e6
        for i,t in enumerate(tr):
            assert t['frame']==tr[0]['frame']+i and abs(t['timestamp']-tr[0]['timestamp']-i*.05)<1e-5
            np.testing.assert_allclose(t['actor_transform']['matrix'],t['snapshot_transform']['matrix'],atol=1e-6,rtol=0)
            excess=max(np.linalg.norm(np.array(v)-t['center'])-body for v in t['world_vertices']);max_body_excess=max(max_body_excess,excess)
            if excess>0:body_failures+=1
            for start in (0,5,10):
                if i<=start or i-start>10:continue
                dt=t['timestamp']-tr[start]['timestamp'];dist=math.hypot(t['center'][0]-tr[start]['center'][0],t['center'][1]-tr[start]['center'][1]);motion_checks+=1;motion_failures+=dist>5*dt+1.5*dt*dt
    trace_checks=[]
    for tr in d['traces']:
        rr=[r for r in d['rows'] if r['episode_id']==tr['episode_id']];t0=rr[0]['source_us'] if rr else 0;expected=queues(rr,tr['method'],tr['bitrate'],t0)
        for k,v in expected.items():assert tr[k]==v,(tr['episode_id'],tr['method'],k)
        ep=byep[tr['episode_id']];hits=model_hits=0
        for decision in tr['decisions']:
            if not decision['grant']:continue
            fr=original[decision['fact_id']];qx=(-6000000,6000000)[decision['query']];end=decision['now_us']+220000
            with localcontext() as ctx:
                ctx.prec=80;x=Decimal.from_float(fr['true_xy'][0])*1000000-qx;y=Decimal.from_float(fr['true_xy'][1])*1000000;dt=Decimal(end-fr['source_us'])/1000000;body=math.ceil(math.sqrt(sum(x*x for x in catalog[fr['blueprint']]))*1e6);reach=Decimal(body+750000)+5000000*dt+1500000*dt*dt;hit=x*x+y*y<=reach*reach
            if hit:model_hits+=1;assert not fr['covered']
            occupied=False
            for state in ep['trajectory']:
                if not decision['now_us']<=qtime(state['timestamp'])<=end:continue
                local=(np.array(state['center'])-fr['anchor'])@np.array(fr['road']);occupied|=math.hypot(local[0]-qx/1e6,local[1])<=(body+750000)/1e6
            hits+=occupied
        trace_checks.append(dict(episode_id=tr['episode_id'],blueprint=tr['blueprint'],bitrate=tr['bitrate'],method=tr['method'],grants=tr['grants'],wire_bytes=tr['wire_bytes'],scheduled_queries=tr['scheduled_queries'],truth_model_reachable_grants=model_hits,observed_disc_occupied_grants=hits))
    for bp in bps:
        ee=[e for e in eps if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in d['rows'] if r['blueprint']==bp and r['split']=='test'];k=sum(any(not r['covered'] for r in rr if r['episode_id']==e['episode']['id']) for e in ee)
        expected=dict(blueprint=bp,**registry[bp],scheduled_test_episodes=60,captured_test_episodes=sum(e['status']=='captured' for e in ee),false_exclusion_episodes=k,available_frames=sum(r['available'] for r in rr),captured_frames=len(rr),scheduled_frames=360);assert expected==next(s for s in d['summary'] if s['blueprint']==bp);summary.append(dict(**expected,one_sided_95_risk_upper=old.risk_upper(k,60)))
    cleanup=read(p/'capture/cleanup.json');assert all(cleanup[k]==0 for k in ('vehicles','walkers','sensors')) and cleanup['synchronous'] is False
    assert len(records)==manifest['frames'] and stored==manifest['stored_rays'] and reported==manifest['original_reported_rays']
    out=dict(summary=summary,trace_checks=trace_checks,scheduled_episodes=930,captured_frames=len(records),stored_rays=stored,original_reported_rays=reported,packet_checks=packets,analytic_age_checks=ages,motion_checks=motion_checks,motion_failures=motion_failures,body_corner_positive_excess_snapshots=body_failures,max_body_corner_excess_um=round(max_body_excess*1e6,6),joint_calibration_confidence_lower=round(1-6*.95**95,15),source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent raster extraction, all saved sampled rays, max95 calibration, frame-local wire, exact model horizon, CPU/link queues and delivered-prefix grants. Body and motion are finite-snapshot audits; positive corner excess is retained. No continuous physical or ego-control safety claim.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('summary','trace_checks')}),flush=True)
if __name__=='__main__':main()
