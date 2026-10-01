#!/usr/bin/env python3
import argparse,csv,gzip,hashlib,json,math,platform,socket,sys
from pathlib import Path
import numpy as np
from model import features,targets,fit,predict,score,calibrate,upper_failure,max_score_confidence,SCALES
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lease_handoff_20261001'))
from lease import Reader,State,contains,ticks,PREFIX,pp


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--packet',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);src=Path(__file__).parent
    manifest=json.loads((a.capture/'manifest.json').read_text());assert manifest['source_file']=='capture_3d.py';assert sha(src/'capture_3d.py')==manifest['source_sha256'] and sha(src/'PROTOCOL.md')==manifest['protocol_sha256'] and sha(src/'POSE_ADDENDUM.md')==manifest['pose_addendum_sha256'];plan=json.loads((a.capture/'plan.json').read_text());assert len(plan)==799 and sha(a.capture/'plan.json')==manifest['plan_sha256'];summaries=list(csv.DictReader((a.capture/'summary.csv').open()));assert len(summaries)==799
    expected=[]
    for role,n,seed in [('train',100,2026100101),('calibration',299,2026100102),('test',400,2026100103)]:
        rng=np.random.Generator(np.random.PCG64(seed))
        for i in range(n):expected.append(dict(id='%s_%04d'%(role,i),role=role,location=int(rng.integers(3)),target=float(rng.uniform(.3,1.2)),prefix_ticks=int(rng.integers(20,160))))
    assert expected==plan
    splits={k:[] for k in ['train','calibration','test']};verified=0;old_acceleration_fail=0
    for request,summary in zip(plan,summaries):
        path=a.capture/'episodes'/(request['id']+'.json.gz');assert summary['id']==request['id'] and sha(path)==summary['sha256'];r=json.loads(gzip.decompress(path.read_bytes()));assert r['request']==request and len(r['rows'])==20+request['prefix_ticks']+41
        previous=r['initial']
        for index,row in enumerate(r['rows']):
            assert row['frame']==previous['frame']+1 and abs(row['timestamp']-previous['timestamp']-.05)<1e-7
            assert abs(row['before_speed']-previous['speed'])<1e-8 and abs(row['acceleration']-(row['speed']-previous['speed'])/.05)<1e-7
            if index<20:assert row['phase']=='warm' and row['command_throttle']==0 and row['command_brake']==1
            elif index<20+request['prefix_ticks']+1:
                assert row['phase']==('prefix' if index<20+request['prefix_ticks'] else 'command')
                v=row['before_speed'];target=request['target'];assert row['command_throttle']==(.45 if v<target else 0.) and row['command_brake']==(min(.2,.2*(v-target)) if v>target+.1 else 0.)
            for key in ['throttle','brake']:assert abs(row['command_'+key]-row['actual_'+key])<1e-6
            assert abs(row['actual_steer'])<1e-7;previous=row;verified+=1
        ref=r['rows'][19+request['prefix_ticks']]
        for key,value in r['reference'].items():assert ref[key]==value
        f=r['features'];assert f['speed']==ref['speed'] and f['last_acceleration']==ref['acceleration'] and f['gear_is_1']==int(ref['actual_gear']==1) and f['target']==request['target']
        command=r['rows'][20+request['prefix_ticks']];assert command['phase']=='command' and command['command_throttle']==f['planned_throttle'] and command['command_brake']==f['planned_brake'];assert all(x['phase']=='backup' and x['command_throttle']==0 and x['command_brake']==1 for x in r['rows'][-40:]);old_acceleration_fail+=command['acceleration']>3+1e-9
        splits[request['role']].append(r)
    assert json.loads((a.capture/'cleanup.json').read_text())==dict(vehicles=0,sensors=0,synchronous=False)
    blob=a.packet.read_bytes();_,n,_,_=PREFIX.unpack_from(blob);h=json.loads(blob[PREFIX.size:PREFIX.size+n]);s=h['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);reader=Reader({k:pp.Profile(**v) for k,v in h['profiles'].items()},pp.Contract(**h['contract']),s['episode'],s['frame_id']);now=h['reference_us']/pp.TIME_SCALE+.13;identity=reader.accept(blob,scope,now);assert identity;region=reader.regions[identity]
    rows=[];models={};reports={}
    for kind in ['constant','state']:
        weights=fit(splits['train'],kind);q=calibrate(splits['calibration'],kind,weights);models[kind]=dict(weights=None if weights is None else weights.tolist(),q=q if math.isfinite(q) else None,finite=math.isfinite(q),scales=SCALES.tolist(),max_score_confidence=max_score_confidence(299),risk_target=.01,guarantee_scope='Fixed random episode distribution, joint sampled extent and finite recorded stop band. Per-method confidence; not selected-state or continuous-time safety.')
        method_rows=[]
        for r in splits['test']:
            y=targets(r);pred=predict(r,kind,weights);bound=pred+q*SCALES;miss=not np.isfinite(y).all() or bool(np.any(y>bound+1e-12));state=State(s['query'][0],s['query'][1],h['yaw'],r['features']['speed']);finite=bool(np.isfinite(bound).all())
            spatial=finite and contains(region,state,np.array([-2-bound[1],-1-bound[2]]),np.array([2+bound[0],1+bound[2]]),.03);timely=finite and ticks(now)+ticks(bound[3])<region.expires_us;admit=spatial and timely
            row=dict(id=r['request']['id'],kind=kind,speed=state.speed,speed_stratum='low' if state.speed<.25 else 'middle' if state.speed<.75 else 'high',joint_exceedance=miss,counterfactual_admit=admit,space=spatial,time=timely,physical_movement_authorized=False)
            for i,key in enumerate(['front_m','rear_m','lateral_m','stop_s']):row['observed_'+key]=float(y[i]) if math.isfinite(y[i]) else None;row['predicted_'+key]=float(bound[i]) if finite else None
            rows.append(row);method_rows.append(row)
        k=sum(r['joint_exceedance'] for r in method_rows);admitted=[r for r in method_rows if r['counterfactual_admit']];strata={}
        for name in ['low','middle','high']:
            subset=[r for r in method_rows if r['speed_stratum']==name];bad=sum(r['joint_exceedance'] for r in subset);strata[name]=dict(n=len(subset),exceedances=bad,upper_95=upper_failure(bad,len(subset)))
        reports[kind]=dict(test_n=len(method_rows),joint_exceedances=k,upper_failure_95=upper_failure(k,len(method_rows)),counterfactual_admissions=len(admitted),exceedances_among_admitted=sum(r['joint_exceedance'] for r in admitted),upper_failure_among_admitted_95=upper_failure(sum(r['joint_exceedance'] for r in admitted),len(admitted)),median_predicted={key:float(np.median([r['predicted_'+key] for r in method_rows])) if math.isfinite(q) else None for key in ['front_m','rear_m','lateral_m','stop_s']},strata=strata)
    with (a.out/'test_predictions.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (a.out/'models.json').write_text(json.dumps(models,indent=2,allow_nan=False)+'\n');report=dict(episodes=799,splits={k:len(v) for k,v in splits.items()},validated_snapshot_rows=verified,actual_command_acceleration_above_3=old_acceleration_fail,source_and_protocol_verified=True,random_plan_reproduced=True,failures_by_split={k:sum(not np.isfinite(targets(r)).all() for r in v) for k,v in splits.items()},methods=reports,physical_movement_authorized=False)
    (a.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');(a.out/'manifest.json').write_text(json.dumps(dict(host=socket.gethostname(),python=platform.python_version(),source_sha256={p.name:sha(p) for p in src.glob('*.py')},protocol_sha256=sha(src/'PROTOCOL.md'),capture_manifest_sha256=sha(a.capture/'manifest.json'),capture_summary_sha256=sha(a.capture/'summary.csv'),packet_sha256=sha(a.packet)),indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
