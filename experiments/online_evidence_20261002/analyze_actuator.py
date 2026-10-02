#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--live',type=Path,required=True);a=ap.parse_args();root=Path(__file__).resolve().parents[2]
    manifest=json.loads((a.capture/'manifest.json').read_text())
    for n,h in manifest['source_sha256'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
    assert hashlib.sha256(Path(__file__).with_name('ACTUATOR_PROTOCOL.md').read_bytes()).hexdigest()==manifest['protocol_sha256']
    live=json.loads(gzip.decompress((a.live/'c0_view0_reference_rate20/record.json.gz').read_bytes()));yaw=math.radians(live['target_yaw']);forward=np.array([math.cos(yaw),math.sin(yaw)])
    rows=[];ticks=0
    for f in sorted(a.capture.glob('*.json.gz')):
        r=json.loads(gzip.decompress(f.read_bytes()));summary=r['summary'];states=r['rows'];go=summary['go_ticks'];manual=summary['mode']=='manual1'
        assert len(states)==15+go+40
        assert np.linalg.norm(np.array([states[14]['x'],states[14]['y']])-np.array(live['target_xyz'][:2]))<.1
        for i,st in enumerate(states):
            throttle=.45 if 15<=i<15+go else 0.;brake=0. if throttle else 1.
            assert st['requested_throttle']==throttle and st['requested_brake']==brake
            assert abs(st['actual_throttle']-throttle)<1e-6 and abs(st['actual_brake']-brake)<1e-6
            assert st['manual_gear_shift']==manual
            if manual:assert st['gear']==1
            if i:assert st['frame']==states[i-1]['frame']+1 and abs(st['timestamp']-states[i-1]['timestamp']-.05)<2e-6
        initial=states[14];end=states[-1];go_end=states[14+go]
        progress=float(np.dot([end['x']-initial['x'],end['y']-initial['y']],forward));go_progress=float(np.dot([go_end['x']-initial['x'],go_end['y']-initial['y']],forward))
        assert progress==summary['progress_m'] and go_progress==summary['go_progress_m']
        assert summary['peak_speed']==max(st['speed'] for st in states[15:]) and summary['collision_count']==len(r['collisions']) and summary['final_speed']==end['speed']
        rows.append(summary);ticks+=len(states)
    assert len(rows)==manifest['episodes']==32 and json.loads((a.capture/'cleanup.json').read_text())==dict(vehicles=0,sensors=0,synchronous=False)
    groups=[]
    for mode in ['automatic','manual1']:
        for go in [1,2,4,8]:
            selected=[r for r in rows if r['mode']==mode and r['go_ticks']==go];assert len(selected)==4
            groups.append(dict(mode=mode,go_ticks=go,episodes=4,median_progress_m=float(np.median([r['progress_m'] for r in selected])),median_peak_speed=float(np.median([r['peak_speed'] for r in selected])),max_final_speed=max(r['final_speed'] for r in selected),collisions=sum(r['collision_count'] for r in selected)))
    result=dict(validation='passed',episodes=len(rows),physics_ticks=ticks,groups=groups,all_actual_controls_verified=True,scope='Finite post-analysis component probes; no calibrated manual-policy maneuver envelope or evidence-guided movement.',analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.capture/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
