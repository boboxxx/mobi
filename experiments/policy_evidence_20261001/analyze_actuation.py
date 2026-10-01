#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np


def read(path):return list(csv.DictReader(path.open()))


def summarize(folder):
    source=read(folder/'summary.csv');out=[]
    for item in source:
        rows=read(folder/'episodes'/(item['id']+'.csv'));drive=[r for r in rows if r['phase']=='drive'];brake=[r for r in rows if r['phase']=='brake']
        assert len(rows)==int(item['rows']) and len(brake)==40
        assert all(abs(float(b['before_speed'])-float(a['speed']))<1e-9 for a,b in zip(rows,rows[1:])), 'State continuity failure'
        stamps=np.array([float(r['timestamp']) for r in rows]);frames=np.array([int(r['frame']) for r in rows]);assert np.all(np.diff(frames)==1) and np.allclose(np.diff(stamps),.05,atol=1e-7,rtol=0)
        speeds=np.array([float(r['speed']) for r in brake]);stop=next((i for i in range(len(speeds)-4) if max(speeds[i:i+5])<=.02),None)
        acceleration=np.array([float(r['sampled_acceleration']) for r in rows]);da=np.array([float(r['sampled_acceleration']) for r in drive]);ba=np.array([float(r['sampled_acceleration']) for r in brake])
        initial=json.loads(item['initial']);yaw=np.array([float(r['yaw']) for r in rows]);yaw=np.radians(np.r_[initial['yaw'],yaw]);yaw_rate=np.diff(np.unwrap(yaw))/.05
        angles=np.array([math.atan2(float(r['vy']),float(r['vx']))-math.radians(float(r['yaw'])) for r in rows]);slips=np.abs(np.arctan2(np.sin(angles),np.cos(angles)));mask=np.array([float(r['speed'])>.02 for r in rows])
        mismatches=None
        if 'actual_throttle' in rows[0]:
            mismatches=sum(any(abs(float(r['actual_'+k])-float(r[k]))>1e-6 for k in ['throttle','brake','steer']) or r['actual_hand_brake']=='True' or r['actual_reverse']=='True' for r in rows)
        stop_claim=.02+(float(brake[0]['before_speed'])+3*.02)/4
        contradictions=sum((i+1)*.05>=stop_claim and float(r['speed'])>.02 for i,r in enumerate(brake))
        out.append(dict(stop_claim_s=stop_claim,stop_claim_violating_samples=contradictions,id=item['id'],target=float(item['target']),target_reached=item['target_reached']=='True',mode=item.get('mode','auto_rpc'),brake_command=float(item['brake']),samples=len(rows),collisions=int(item['collisions']),drive_max_acceleration=float(max(da)),brake_min_acceleration=float(min(ba)),absolute_acceleration_8_violations=int(np.sum(np.abs(acceleration)>8.+1e-5)),traction_3_violations=int(np.sum(da>3.+1e-5)),brake_entry_speed=float(brake[0]['before_speed']),brake_peak_speed=float(max(speeds)),stop_band_upper_s=None if stop is None else (stop+1)*.05,maximum_yaw_rate=float(max(np.abs(yaw_rate))),maximum_slip_above_band=float(max(slips[mask])) if mask.any() else None,slip_003_violations=int(np.sum(slips[mask]>.03)),control_readback_mismatches=mismatches,readback_recorded='actual_throttle' in rows[0]))
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();src=Path(__file__).parent;results={}
    for folder,script,protocol in [('actuation','capture_actuation.py','CALIBRATION_PROTOCOL.md'),('drivetrain','capture_drivetrain.py','DRIVETRAIN_PROTOCOL.md'),('sensitivity','capture_sensitivity.py','ACTUATOR_FOLLOWUP.md')]:
        manifest=json.loads((a.results/folder/'manifest.json').read_text())
        assert hashlib.sha256((src/script).read_bytes()).hexdigest()==manifest['source_sha256']
        assert hashlib.sha256((src/protocol).read_bytes()).hexdigest()==manifest['protocol_sha256']
        cleanup=json.loads((a.results/folder/'cleanup.json').read_text());assert cleanup==dict(vehicles=0,sensors=0,synchronous=False)
        rows=summarize(a.results/folder)
        assert len(rows)==manifest['episodes']
        results[folder]=dict(episodes=len(rows),targets_reached=sum(r['target_reached'] for r in rows),collisions=sum(r['collisions'] for r in rows),stop_claim_violating_episodes=sum(r['stop_claim_violating_samples']>0 for r in rows),sampled_traction_3_violations=sum(r['traction_3_violations'] for r in rows),sampled_absolute_8_violations=sum(r['absolute_acceleration_8_violations'] for r in rows),control_readback_mismatches=sum(r['control_readback_mismatches'] for r in rows) if all(r['readback_recorded'] for r in rows) else None,details=rows)
    for name in ['server_cleanup.json','server_cleanup_drivetrain.json','server_cleanup_sensitivity.json']:assert not json.loads((a.results/name).read_text())['own_server_remaining']
    results['validation']='passed';results['scope']='Discrete own-vehicle telemetry falsifies specified dynamics bounds; absence of sampled violations does not calibrate continuous physics. No certificate-guided driving.'
    (a.results/'actuation_analysis.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k: {kk:vv for kk,vv in v.items() if kk!='details'} if isinstance(v,dict) else v for k,v in results.items()},indent=2))


if __name__=='__main__':main()
