#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();root=a.results/'control';src=Path(__file__).parent
    manifest=json.loads((root/'manifest.json').read_text());assert manifest['source_sha256']==hashlib.sha256((src/'capture_control.py').read_bytes()).hexdigest();assert manifest['protocol_sha256']==hashlib.sha256((src/'CONTROL_PROTOCOL.md').read_bytes()).hexdigest()
    cleanup=json.loads((root/'cleanup.json').read_text());assert cleanup==dict(vehicles=0,sensors=0,synchronous=False)
    summaries=list(csv.DictReader((root/'summary.csv').open()));assert len(summaries)==12;out=[]
    for s in summaries:
        rows=list(csv.DictReader((root/'episodes'/(s['id']+'.csv')).open()));assert len(rows)==200
        initial=json.loads(s['initial']);previous=initial
        for r in rows:
            assert int(r['frame'])==int(previous['frame'])+1
            assert abs(float(r['timestamp'])-float(previous['timestamp'])-.05)<1e-7
            assert abs(float(r['before_speed'])-float(previous['speed']))<1e-8
            assert abs(float(r['sampled_acceleration'])-(float(r['speed'])-float(previous['speed']))/.05)<1e-7
            if r['phase']=='backup' or s['mode']=='relay':
                for k in ['throttle','brake']:assert abs(float(r[k])-float(r['actual_'+k]))<1e-6
            assert abs(float(r['actual_steer']))<1e-7;previous=r
        assert all(r['phase']=='drive' for r in rows[:160]) and all(r['phase']=='backup' for r in rows[160:])
        assert float(s['box_x'])+abs(float(s['box_offset_x']))<=2 and float(s['box_y'])+abs(float(s['box_offset_y']))<=1
        drive=rows[:160];backup=rows[160:];speeds=np.array([float(r['speed']) for r in drive]);tail=speeds[80:];acc=np.array([float(r['sampled_acceleration']) for r in drive]);yaw=math.radians(initial['yaw']);forward=np.array([math.cos(yaw),math.sin(yaw)])
        xy=lambda r:np.array([float(r['x']),float(r['y'])]);progress=float(np.dot(xy(drive[-1])-xy(initial),forward));backup_progress=float(np.dot(xy(backup[-1])-xy(drive[-1]),forward))
        band=next((i for i in range(len(backup)-4) if all(float(r['speed'])<=.02 for r in backup[i:i+5])),None)
        out.append(dict(id=s['id'],mode=s['mode'],target=float(s['target']),drive_progress_m=progress,mean_speed_last_4s=float(tail.mean()),rmse_target_last_4s=float(np.sqrt(np.mean((tail-float(s['target']))**2))),max_speed=float(speeds.max()),max_sampled_acceleration=float(acc.max()),acceleration_above_3_samples=int((acc>3+1e-9).sum()),backup_start_speed=float(drive[-1]['speed']),backup_progress_m=backup_progress,first_5_sample_band_s=None if band is None else (band+1)*.05,post_band_max_speed=None if band is None else max(float(r['speed']) for r in backup[band:]),final_speed=float(backup[-1]['speed']),collisions=int(s['collisions']),box_inside_stipulated_body=True))
    with (a.results/'control_analysis.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    report=dict(episodes=len(out),snapshot_continuity_checks=2400,source_and_protocol_hashes_match=True,raw_relay_and_backup_controls_match=True,episodes_above_traction3=sum(r['acceleration_above_3_samples']>0 for r in out),all_have_five_sample_stop_band=all(r['first_5_sample_band_s'] is not None for r in out),collision_events=sum(r['collisions'] for r in out),cleanup=cleanup,scope='Actual short empty-scene controls. Desired acceleration is not a hard bound. Neither continuous-time calibration, statistical coverage nor evidence-guided driving.')
    (a.results/'control_analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
