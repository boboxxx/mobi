#!/usr/bin/env python3
"""Independent raster components, center coverage, packet and analytic-age audit."""
import argparse,hashlib,json,math,struct
from decimal import Decimal,localcontext,ROUND_CEILING
from pathlib import Path
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
HEADER=struct.Struct('<4sHHIIdI32s32s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def risk_upper(k,n):
    if k==n:return 1.
    with localcontext() as ctx:
        ctx.prec=80;lo=Decimal(0);hi=Decimal(1)
        for _ in range(100):
            mid=(lo+hi)/2;c=sum(Decimal(math.comb(n,i))*mid**i*(1-mid)**(n-i) for i in range(k+1))
            if c>Decimal('.05'):lo=mid
            else:hi=mid
        return round(float(hi),15)


def proposals(raw,matrix,anchor,yaw,ext):
    xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)
    world=xyz[:,0,None]*matrix[:3,0]+xyz[:,1,None]*matrix[:3,1]+xyz[:,2,None]*matrix[:3,2]+matrix[:3,3]
    d=world-anchor;c=math.cos(yaw);s=math.sin(yaw);local=np.c_[d[:,0]*c+d[:,1]*s,-d[:,0]*s+d[:,1]*c,d[:,2]]
    p=local[(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3)]
    if not len(p):return np.empty((0,2)),dict(selected=0,components=0,retained=0)
    ij=np.floor(p[:,:2]/.2).astype(int);offset=ij.min(axis=0);indices=ij-offset;grid=np.zeros(tuple(indices.max(axis=0)+1),bool);grid[tuple(indices.T)]=True;labels,n=ndimage.label(grid,structure=np.ones((3,3),int));point_labels=labels[tuple(indices.T)];out=[]
    for label in range(1,n+1):
        pp=p[point_labels==label];low=pp.min(axis=0);high=pp.max(axis=0)
        if len(pp)>=3 and max(high[0]-low[0],high[1]-low[1])<=2*math.sqrt(sum(x*x for x in ext))+.2 and high[2]-low[2]<=2*ext[2]+.2:out.append((low[:2]+high[:2])/2)
    return np.array(out).reshape(-1,2),dict(selected=len(p),components=int(n),retained=len(out))

def horizon(cm,radius,ext,qx):
    body=math.ceil(math.sqrt(sum(float(x)*float(x) for x in ext))*1e6);lower=500000;upper=500000
    for c in cm:
        x=int(c[0])*10000-qx;y=int(c[1])*10000;rad=int(radius)+body+750000
        with localcontext() as ctx:
            ctx.prec=80;gap=Decimal(x*x+y*y).sqrt()-Decimal(rad)
            if gap<=0:return 0,0
            t=(Decimal(25000000000000)+Decimal(6000000)*gap).sqrt()-Decimal(5000000);t=t/Decimal(3000000)*Decimal(1000000)
            if t>500000:lo=up=500000
            else:up=int(t.to_integral_value(rounding=ROUND_CEILING));lo=max(0,up-1)
        def safe(us):
            rr=2000000*rad+10000000*us+3*us*us
            return (x*x+y*y)*4000000000000>rr*rr
        assert safe(lo) and (lo==500000 or not safe(lo+1))
        if lo<lower:lower,upper=lo,up
    return lower,upper

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();analysis=json.loads((p/'analysis_sheng.json').read_bytes());records=json.loads((p/'capture/record.json').read_bytes());plan=json.loads((HERE/'plan.json').read_bytes());catalog=json.loads((HERE/'catalog.json').read_bytes());bps=list(catalog);freeze=json.loads((HERE/'capture_freeze.json').read_bytes());manifest=json.loads((p/'capture/manifest.json').read_bytes())
    for mapping in (freeze['source_hashes'],analysis['source_hashes'],analysis['input_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    for name,key in [('capture.py','source_sha256'),('plan.json','plan_sha256'),('model.py','model_sha256'),('PROTOCOL.md','protocol_sha256')]:assert sha(HERE/name)==manifest[key]
    assert sha(p/'capture/manifest.json')==analysis['capture_manifest_sha256'];generated=[]
    for j,bp in enumerate(bps):
        for split,n,base in [('calibration',39,2026100700),('test',60,2026100800)]:
            rng=np.random.default_rng(base+j)
            for i in range(n):generated.append(dict(id=bp.replace('.','_')+'_'+split+'_%02d'%i,blueprint=bp,split=split,index=i,seed=base+j,longitudinal_m=float(rng.uniform(-8,8)),lateral_m=float(rng.uniform(-4,4)),yaw_deg=float(rng.uniform(0,360))))
    assert generated==plan and len(plan)==594;record_by_episode={};frame_checks={};raw_rays=0;original_rays=0
    for r in records:
        ep=next(e for e in plan if e['id']==r['episode']['id']);assert ep==r['episode'];record_by_episode.setdefault(ep['id'],[]).append(r)
        if r['status']!='captured':assert r['status'] in ('spawn_failed','missing_blueprint');continue
        path=p/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256'];z=np.load(path);raw=z['raw'];matrix=z['transform'];assert r['sampling_stride']==4 and len(raw)==r['points']==(r['original_points']+3)//4;raw_rays+=len(raw);original_rays+=r['original_points'];assert np.isfinite(np.c_[raw['x'],raw['y'],raw['z']]).all();np.testing.assert_array_equal(matrix,r['sensor_transform']['matrix']);np.testing.assert_array_equal(z['origin'],matrix[:3,3]);assert float(z['timestamp'])==r['timestamp']==r['snapshot_timestamp'];assert r['frame']==r['sensor_frame']==r['snapshot_frame'];assert int(np.sum(raw['id']==r['actor_id']))==r['actor_returns'];np.testing.assert_array_equal(r['bounding_box']['extent'],catalog[r['blueprint']]);np.testing.assert_allclose(r['actor_transform']['matrix'],r['snapshot_transform']['matrix'],rtol=0,atol=1e-5);center=np.asarray(r['actor_transform']['matrix'])@np.r_[r['bounding_box']['location'],1.];np.testing.assert_allclose(center[:3],r['center'],rtol=0,atol=1e-5)
        anchor=np.r_[r['query'],0.];yaw=math.radians(r['road_yaw']);np.testing.assert_array_equal(anchor,analysis['contract_body']['basis']['anchor']);np.testing.assert_array_equal([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1]],analysis['contract_body']['basis']['road']);c,meta=proposals(raw,matrix,anchor,yaw,catalog[r['blueprint']]);d=np.asarray(r['center'])-anchor;true=np.array([d[0]*math.cos(yaw)+d[1]*math.sin(yaw),-d[0]*math.sin(yaw)+d[1]*math.cos(yaw)]);fr=next(x for x in analysis['rows'] if x['id']==r['id']);np.testing.assert_allclose(c,np.asarray(fr['centers']).reshape(-1,2),rtol=0,atol=1e-10);cm=np.rint(c*100).astype(np.int32);np.testing.assert_array_equal(cm,np.asarray(fr['centers_cm']).reshape(-1,2));assert meta==fr['metadata'];np.testing.assert_allclose(true,fr['true_xy'],rtol=0,atol=1e-10);frame_checks[r['id']]=dict(centers=c,cm=cm,true=true,source=r)
    episodes=[];registry={}
    for ep in plan:
        rr=record_by_episode.get(ep['id'],[]);fr=[frame_checks[r['id']] for r in rr if r['status']=='captured'];available=len(fr)==2 and {f['source']['layout'] for f in fr}=={0,1} and all(len(f['centers']) for f in fr);residual=max(min(math.hypot(*(c-f['true'])) for c in f['centers']) for f in fr) if available else 0.;expected=next(e for e in analysis['episodes'] if e['id']==ep['id']);assert available==expected['available'] and abs(residual-expected['residual_m'])<1e-10;episodes.append(dict(id=ep['id'],blueprint=ep['blueprint'],split=ep['split'],available=bool(available),residual=residual,frames=[f['source']['id'] for f in fr],excluded=False,zero_excluded=False))
    for bp in bps:
        cal=[e['residual'] for e in episodes if e['blueprint']==bp and e['split']=='calibration'];radius=math.ceil(sorted(cal)[37]*1e6+1e-7)+8000;registry[bp]=dict(radius_um=radius,rank=38,calibration_n=39)
    assert registry==analysis['registry'];digest=hashlib.sha256(json.dumps(registry,sort_keys=True,separators=(',',':')).encode()).hexdigest();contract=hashlib.sha256(json.dumps(analysis['contract_body'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert digest==analysis['calibration_sha256'] and contract==analysis['contract_sha256'];assert analysis['contract_body']['catalog']==catalog and analysis['contract_body']['model_sha256']==sha(HERE/'model.py') and analysis['contract_body']['protocol_sha256']==sha(HERE/'PROTOCOL.md');age_checks=0;packet_checks=0;rows_out=[]
    for fr in analysis['rows']:
        f=frame_checks[fr['id']];ep=next(e for e in episodes if e['id']==fr['episode']);r=f['source'];radius=registry[fr['blueprint']]['radius_um'];wire=(p/fr['packet']).read_bytes();assert len(wire)==fr['wire_bytes'] and hashlib.sha256(wire).hexdigest()==fr['packet_sha256'] and hashlib.sha256(wire[:-32]).digest()==wire[-32:];h=HEADER.unpack(wire[:HEADER.size]);n=struct.unpack('<I',wire[HEADER.size:HEADER.size+4])[0];assert h[:2]==(b'PCS1',1) and h[2]==int(not ep['available']) and h[3]==bps.index(fr['blueprint']) and h[4]==r['frame']==fr['frame'] and h[5]==r['timestamp']==fr['source_timestamp'] and h[7].hex()==contract and h[8].hex()==digest;assert len(wire)==HEADER.size+4+8*n+32;cm=np.frombuffer(wire,dtype='<i4',count=2*n,offset=HEADER.size+4).reshape(-1,2)
        if ep['available']:
            assert h[6]==radius and n>0;np.testing.assert_array_equal(cm,f['cm']);rounding=np.linalg.norm(cm/100.-f['centers'],axis=1);assert np.all(rounding<=.008);distance=min(math.hypot(*(c/100.-f['true'])) for c in cm);covered=distance*1e6<=radius;zero=distance<=.008;ep['excluded']|=not covered;ep['zero_excluded']|=not zero
        else:assert h[6]==n==0;covered=zero=True
        assert fr['covered']==covered and fr['zero_covered']==zero and fr['available']==ep['available'];packet_checks+=1;ext=catalog[fr['blueprint']];truth_cm=np.rint(f['true']*100).astype(np.int32)[None,:]
        for label,points,rad,refused in [('bounds',cm,radius,not ep['available']),('zero_radius_diagnostic',f['cm'],8000,not ep['available']),('truth_center_oracle',truth_cm,8000,False)]:
            for j,qx in enumerate((-6000000,6000000)):
                lo,up=(0,500000) if refused else horizon(points,rad,ext,qx);b=fr[label][j];assert (lo,up)==(b['lower_us'],b['upper_us']);age_checks+=1
        expected_cost=math.ceil(240000+r['acquisition_s']*1e6+max(t['pipeline_s'] for t in fr['timings'])*1e6+len(wire)*.4);assert expected_cost==fr['cost_us'];assert fr['modeled_remaining_us']==[max(0,b['lower_us']-expected_cost) for b in fr['bounds']];rows_out.append(dict(id=fr['id'],available=ep['available'],covered=covered,centers=len(cm),radius_um=radius,bounds=fr['bounds'],modeled_remaining_us=fr['modeled_remaining_us']))
    summary={}
    for ep in episodes:
        original=next(e for e in analysis['episodes'] if e['id']==ep['id']);assert ep['excluded']==original['excluded'] and ep['zero_excluded']==original['zero_excluded']
    for bp in bps:
        test=[e for e in episodes if e['blueprint']==bp and e['split']=='test'];k=sum(e['excluded'] for e in test);available=sum(e['available'] for e in test);tr=[r for r in analysis['rows'] if r['blueprint']==bp and r['split']=='test'];expected=dict(**registry[bp],scheduled=60,available=available,refused=60-available,false_exclusion_episodes=k,zero_radius_false_exclusion_episodes=sum(e['zero_excluded'] for e in test),unconditional_one_sided_95_upper=risk_upper(k,60),conditional_available_one_sided_95_upper=risk_upper(k,available),positive_modeled_query_results=sum(n>0 for r in tr for n in r['modeled_remaining_us']),scheduled_query_results=240,captured_query_results=2*len(tr),available_query_results=4*available,positive_query_results_on_excluded_episodes=sum(n>0 for r in tr if next(e['excluded'] for e in test if e['id']==r['episode']) for n in r['modeled_remaining_us']));original=analysis['summary'][bp];assert all(abs(expected[key]-original[key])<1e-12 if key.endswith('_upper') else expected[key]==original[key] for key in expected);summary[bp]=expected
    cleanup=json.loads((p/'capture/cleanup.json').read_bytes());assert cleanup['vehicles']==cleanup['walkers']==cleanup['sensors']==0 and not cleanup['synchronous'];assert len(frame_checks)==manifest['captured'] and len(records)==manifest['rows'];result=dict(summary=summary,rows=rows_out,scheduled_episodes=len(plan),captured_frames=len(frame_checks),stored_rays=raw_rays,original_reported_rays=original_rays,packet_checks=packet_checks,analytic_age_checks=age_checks,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent raster-connected-components extraction, all stored XYZ points, source/label alignment, frozen draws/quantiles/family coverage, exact packet reconstruction and analytic+integer contact times. Counterexample and physical safety claims not inferred from marginal coverage. No semantic labels enter extraction; IDs only verify capture records.');a.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
