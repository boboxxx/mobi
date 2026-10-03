#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
from scipy.stats import beta
from model import centers,quantized_centers,score,radius_um
from codec import encode,decode
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exact_disc_lifetime',ROOT/'experiments/shape_evidence_20261002/lifetime.py');life=importlib.util.module_from_spec(spec);sys.modules[spec.name]=life;spec.loader.exec_module(life)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geometry(c_cm,radius,ext,refused=False):
    if refused or not len(c_cm):return [dict(lower_us=0,upper_us=500000,reason='refused') for _ in range(2)]
    body=math.ceil(float(np.linalg.norm(ext))*1e6);states=[life.State(int(c[0])*10000,int(c[1])*10000,int(radius)+body,5000000,3000000) for c in c_cm];out=[]
    for qx in (-6000000,6000000):
        # Complete support of this calibrated known-object model, not a scene inventory claim.
        r=life.expiry(states,(qx,0),750000,500000,complete_support=True);low=r['safe_through_us'];up=low if r['reason']=='unsafe_at_observation' or r['capped'] else low+1;out.append(dict(lower_us=low,upper_us=up,reason=r['reason'],witness_index=r['witness_index']))
    return out

def frame_input(row,path,ext):
    with np.load(path) as z:raw=z['raw'];matrix=z['transform'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)
    anchor=np.r_[row['query'],0.];yaw=math.radians(row['road_yaw']);road=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1.]])
    return xyz,np.asarray(matrix),anchor,road

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--label',default='sheng');a=ap.parse_args();p=a.results.resolve();capture=p/'capture';rows=json.loads((capture/'record.json').read_bytes());plan=json.loads((HERE/'plan.json').read_bytes());catalog=json.loads((HERE/'catalog.json').read_bytes());bps=list(catalog);frames={};episode_rows={};inputs={};compute=[]
    for row in rows:
        episode_rows.setdefault(row['episode']['id'],[]).append(row)
        if row['status']!='captured':continue
        path=capture/row['cloud_file'];assert sha(path)==row['cloud_sha256'];inputs[str(path.relative_to(ROOT))]=sha(path);assert row['sampling_stride']==4;xyz,matrix,anchor,road=frame_input(row,path,catalog[row['blueprint']]);world=xyz@matrix[:3,:3].T+matrix[:3,3];c,meta=centers(world,anchor,road,catalog[row['blueprint']]);true=(np.asarray(row['center'])-anchor)@road;frames[row['id']]=dict(centers=c,centers_cm=quantized_centers(c),meta=meta,true_xy=true[:2],source=row,path=path,anchor=anchor,road=road)
    episodes=[]
    for ep in plan:
        rr=episode_rows.get(ep['id'],[]);fr=[frames[r['id']] for r in rr if r['status']=='captured'];available=len(fr)==2 and {f['source']['layout'] for f in fr}=={0,1} and all(len(f['centers']) for f in fr);residual=max(score(f['centers'],f['true_xy']) for f in fr) if available else 0.
        episodes.append(dict(id=ep['id'],blueprint=ep['blueprint'],split=ep['split'],available=bool(available),residual_m=residual,frames=[f['source']['id'] for f in fr],capture_status=[r['status'] for r in rr]))
    registry={}
    for bp in bps:
        cal=[e['residual_m'] for e in episodes if e['blueprint']==bp and e['split']=='calibration'];assert len(cal)==39;registry[bp]=dict(radius_um=radius_um(cal),rank=38,calibration_n=39)
    calibration=hashlib.sha256(json.dumps(registry,sort_keys=True,separators=(',',':')).encode()).hexdigest();basis={f['source']['id']:dict(anchor=f['anchor'].tolist(),road=f['road'].tolist()) for f in frames.values()};unique={json.dumps(v,sort_keys=True) for v in basis.values()};assert len(unique)==1,'Unexpected coordinate contract change';contract_body=dict(catalog=catalog,basis=json.loads(next(iter(unique))),model_sha256=sha(HERE/'model.py'),protocol_sha256=sha(HERE/'PROTOCOL.md'));contract=hashlib.sha256(json.dumps(contract_body,sort_keys=True,separators=(',',':')).encode()).hexdigest();packetdir=p/('messages_'+a.label);packetdir.mkdir(exist_ok=False);out=[]
    for ep in episodes:
        radius=registry[ep['blueprint']]['radius_um'];excluded=False;zero_excluded=False
        for key in ep['frames']:
            f=frames[key];row=f['source'];ext=catalog[ep['blueprint']];xyz,matrix,anchor,road=frame_input(row,f['path'],ext);timings=[];previous=None
            for repeat in range(3):
                start=time.perf_counter();world=xyz@matrix[:3,:3].T+matrix[:3,3];c,meta=centers(world,anchor,road,ext);cm=quantized_centers(c);wire=encode(cm,radius,row['frame'],row['timestamp'],bps.index(ep['blueprint']),contract,calibration,refused=not ep['available']);decoded=decode(wire,contract,calibration,bps.index(ep['blueprint']),radius);bounds=geometry(decoded['centers_cm'],decoded['radius_um'],ext,decoded['refused']);seconds=time.perf_counter()-start;timings.append(dict(repeat=repeat,pipeline_s=seconds))
                if previous is not None:assert previous==wire
                previous=wire
            if ep['available']:
                actual_distance=float(np.min(np.linalg.norm(cm/100.-f['true_xy'],axis=1)));covered=actual_distance*1e6<=radius;zero_covered=actual_distance<=.008;excluded|=not covered;zero_excluded|=not zero_covered
            else:actual_distance=None;covered=True;zero_covered=True
            name=key+'.bin';(packetdir/name).write_bytes(wire);base=240000+row['acquisition_s']*1e6+max(t['pipeline_s'] for t in timings)*1e6+len(wire)*.4;net=[max(0,b['lower_us']-math.ceil(base)) for b in bounds];oracle=geometry(quantized_centers([f['true_xy']]),8000,ext);zero=geometry(cm,8000,ext,not ep['available']);out.append(dict(id=key,episode=ep['id'],blueprint=ep['blueprint'],split=ep['split'],layout=row['layout'],available=ep['available'],centers=f['centers'].tolist(),centers_cm=cm.tolist(),radius_um=radius,metadata=f['meta'],true_xy=f['true_xy'].tolist(),nearest_quantized_distance_m=actual_distance,covered=bool(covered),zero_covered=bool(zero_covered),frame=row['frame'],source_timestamp=row['timestamp'],packet=str((packetdir/name).relative_to(p)),packet_sha256=hashlib.sha256(wire).hexdigest(),wire_bytes=len(wire),bounds=bounds,zero_radius_diagnostic=zero,truth_center_oracle=oracle,modeled_remaining_us=net,cost_us=math.ceil(base),acquisition_s=row['acquisition_s'],timings=timings));print('frame',key,'available',ep['available'],'radius',radius,'covered',covered,'remaining',net,flush=True)
        ep['excluded']=bool(excluded);ep['zero_excluded']=bool(zero_excluded)
    summary={}
    for bp in bps:
        test=[e for e in episodes if e['blueprint']==bp and e['split']=='test'];assert len(test)==60;k=sum(e['excluded'] for e in test);available=sum(e['available'] for e in test);tr=[r for r in out if r['blueprint']==bp and r['split']=='test'];summary[bp]=dict(**registry[bp],scheduled=60,available=available,refused=60-available,false_exclusion_episodes=k,zero_radius_false_exclusion_episodes=sum(e['zero_excluded'] for e in test),unconditional_one_sided_95_upper=float(beta.ppf(.95,k+1,60-k)) if k<60 else 1.,conditional_available_one_sided_95_upper=float(beta.ppf(.95,k+1,available-k)) if k<available else 1.,positive_modeled_query_results=sum(n>0 for r in tr for n in r['modeled_remaining_us']),scheduled_query_results=240,captured_query_results=2*len(tr),available_query_results=4*available,positive_query_results_on_excluded_episodes=sum(n>0 for r in tr if next(e['excluded'] for e in test if e['id']==r['episode']) for n in r['modeled_remaining_us']))
    deps=[HERE/f for f in ('model.py','codec.py','evaluate.py','PROTOCOL.md','plan.json','catalog.json')]+[ROOT/'experiments/shape_evidence_20261002/lifetime.py'];result=dict(rows=out,episodes=episodes,summary=summary,registry=registry,contract_body=contract_body,contract_sha256=contract,calibration_sha256=calibration,input_hashes=inputs,source_hashes={str(f.relative_to(ROOT)):sha(f) for f in deps},capture_manifest_sha256=sha(capture/'manifest.json'),scope='Fresh wider-position static known-class center-set coverage. XYZ-only sender, calibrated union of quantized discs, simultaneous two-view marginal coverage under exchangeability. Full episode availability uses both completed views, not a causal online family schedule. Geometry exact only within the center-union/body-disc model. No full scene inventory, physical safety, trajectory risk or live control claim.');(p/('analysis_'+a.label+'.json')).write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
