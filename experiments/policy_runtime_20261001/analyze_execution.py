#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from incremental import pp
from tube import envelope,policy_limits


def read(path):return list(csv.DictReader(path.open()))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();root=a.results/'execution';src=Path(__file__).parent
    manifest=json.loads((root/'manifest.json').read_text())
    assert hashlib.sha256((src/'capture_execution.py').read_bytes()).hexdigest()==manifest['source_sha256']
    assert hashlib.sha256((src/'EXECUTION_PROTOCOL.md').read_bytes()).hexdigest()==manifest['protocol_sha256']
    assert json.loads((root/'cleanup.json').read_text())==dict(vehicles=0,sensors=0,synchronous=False)
    assert not json.loads((a.results/'server_cleanup.json').read_text())['own_server_remaining']
    summaries=read(root/'summary.csv');details=[];pairs={};policy=pp.Policy()
    for item in summaries:
        raw=read(root/'episodes'/(item['id']+'.csv'));assert len(raw)==int(item['rows'])
        assert all(int(b['frame'])-int(a['frame'])==1 and abs(float(b['timestamp'])-float(a['timestamp'])-.05)<1e-7 for a,b in zip(raw,raw[1:]))
        assert all(abs(float(r['actual_'+k])-float(r[k]))<1e-6 for r in raw for k in ['throttle','brake'])
        assert all(abs(float(r['actual_steer']))<1e-6 and r['actual_hand_brake']=='False' and r['actual_reverse']=='False' for r in raw)
        rows=[r for r in raw if r['phase']!='prepare'];ref=json.loads(item['reference']);hold=float(item['hold']);speed=ref['speed'];yaw=math.radians(ref['yaw']);rot=pp.rotation(yaw)
        assert int(rows[0]['frame'])==ref['frame']+1
        xy=np.array([[float(r['x'])-ref['x'],float(r['y'])-ref['y']] for r in rows])@rot
        frame_time=np.array([(int(r['frame'])-ref['frame'])*.05 for r in rows]);speeds=np.array([float(r['speed']) for r in rows])
        low,high,margin=envelope(speed,.4,0.,policy)
        extent=np.array([float(item['box_x']),float(item['box_y'])]);offset=np.array([float(item['box_offset_x']),float(item['box_offset_y'])])
        boxrot=pp.rotation(math.radians(float(item['box_yaw'])))
        corners=np.array([[x,y] for x in [-extent[0],extent[0]] for y in [-extent[1],extent[1]]])@boxrot.T+offset
        body_fits=bool(np.all(np.abs(corners)<=np.array([policy.half_length,policy.half_width])))
        violation=0.
        for i,row in enumerate(rows):
            if frame_time[i]>.4+1e-9:continue
            actual=corners@pp.rotation(math.radians(float(row['yaw']))-yaw).T+xy[i]
            distance=np.linalg.norm(np.maximum(np.maximum(low-actual,actual-high),0),axis=1)
            violation=max(violation,float(np.max(distance-margin)))
        _,claimed_time=policy_limits(speed,hold,policy)
        stop_index=next((i for i,r in enumerate(rows) if r['phase']=='backup' and i+5<=len(rows) and max(speeds[i:i+5])<=.02),None)
        go_index=next(i for i,r in enumerate(rows) if r['phase']=='go');before_go=xy[go_index-1]
        d=dict(id=item['id'],go=item['go']=='True',location=int(item['location']),target=float(item['target']),hold=hold,reference_speed=speed,reference_state=ref,target_reached=item['target_reached']=='True',body_fits=body_fits,collisions=int(item['collisions']),forward_total=float(xy[-1,0]),forward_after_hold=float(xy[-1,0]-before_go[0]),max_sampled_displacement=float(np.max(np.linalg.norm(xy,axis=1))),claimed_complete_s=claimed_time,stop_band_upper_s=None if stop_index is None else float(frame_time[stop_index]),samples_moving_after_claim=int(np.sum((frame_time>=claimed_time)&(speeds>.02))),maximum_sampled_tube_excess_m=violation)
        details.append(d);pairs.setdefault((d['location'],d['target'],hold),{})[d['go']]=d
    paired=[]
    for key,pair in sorted(pairs.items()):
        assert set(pair)=={True,False};go=pair[True];stop=pair[False]
        mismatch=max(abs(go['reference_state'][k]-stop['reference_state'][k]) for k in ['x','y','yaw','vx','vy','speed'])
        paired.append(dict(location=key[0],target=key[1],hold=key[2],reference_max_difference=mismatch,incremental_forward_m=go['forward_total']-stop['forward_total'],go_forward_m=go['forward_total'],stop_forward_m=stop['forward_total']))
    assert len(details)==manifest['episodes']==36 and len(paired)==18
    out=dict(validation='passed',episodes=36,pairs=18,targets_reached=sum(d['target_reached'] for d in details),collisions=sum(d['collisions'] for d in details),body_fit_failures=sum(not d['body_fits'] for d in details),sampled_tube_violations=sum(d['maximum_sampled_tube_excess_m']>1e-6 for d in details),claimed_stop_violating_episodes=sum(d['samples_moving_after_claim']>0 for d in details),maximum_pair_reference_difference=max(p['reference_max_difference'] for p in paired),paired=paired,details=details,scope='Actual specified-policy and brake-only diagnostics; sampled containment is not continuous hard-bound calibration; no evidence-driven actions.')
    (a.results/'execution_analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['details','paired']},indent=2));print(json.dumps(paired,indent=2))


if __name__=='__main__':main()
