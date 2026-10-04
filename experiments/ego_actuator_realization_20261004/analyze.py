#!/usr/bin/env python3
"""Independent pose/control/time reconstruction from actual recorded snapshots."""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

E = Path(__file__).resolve().parent
ROOT = E.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rotation(angles):
    p, y, r = map(math.radians, angles)
    cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(r), math.sin(r)
    return [[cp*cy, cy*sp*sr-sy*cr, -cy*sp*cr-sy*sr],
            [cp*sy, sy*sp*sr+cy*cr, -sy*sp*cr+cy*sr],
            [sp, -cp*sr, cp*cr]]


def transform(R, p, offset):
    return [sum(a*b for a,b in zip(row,p))+o for row,o in zip(R,offset)]


def norm(v):
    return math.sqrt(sum(x*x for x in v))


def distance(a,b):
    return norm([x-y for x,y in zip(a,b)])


def median(vals):
    ordered=sorted(vals);n=len(ordered)
    return (ordered[n//2]+ordered[(n-1)//2])/2


def stop_index(rows):
    """First low-speed state followed by two more low-speed states, or refusal."""
    for i in range(len(rows)-2):
        if all(math.hypot(*r['velocity'][:2]) <= .02 for r in rows[i:i+3]):
            return i
    return None


def body_error(body, row):
    R, B = rotation(row['rotation']), rotation(body['rotation'])
    center = transform(R,body['offset'],row['location'])
    assert distance(center,row['center']) < .0002
    for i in range(3):
        for j in range(3):
            assert abs(R[i][j]-row['matrix'][i][j]) < 2e-6
    corners = [transform(R,transform(B,v,body['offset']),row['location']) for v in itertools.product(*[(-e,e) for e in body['extent']])]
    actual = row['body_vertices']
    assert len(actual)==len(corners)==8
    # CARLA's corner order is independent of this auditor's enumeration.
    error = max(min(distance(p,q) for q in actual) for p in corners)
    reverse = max(min(distance(p,q) for q in corners) for p in actual)
    assert max(error,reverse) < .0002
    return max(error,reverse)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert not a.out.exists()
    frozen=json.loads((E/'freeze.json').read_bytes())
    for section in ('sources','inputs'):
        for n,h in frozen[section].items():
            assert sha(ROOT/n)==h,n
    plan=json.loads((E/'plan.json').read_bytes());outcomes=json.loads((a.capture/'outcomes.json').read_bytes());spawns=json.loads((a.capture/'spawns.json').read_bytes())
    assert len(plan)==len(outcomes)==36 and [v['request'] for v in outcomes]==plan
    assert (a.capture/'plan.json').read_bytes()==(E/'plan.json').read_bytes()
    assert json.loads((a.capture/'cleanup.json').read_bytes())==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
    manifest=json.loads((a.capture/'manifest.json').read_bytes());assert manifest['freeze_sha256']==sha(E/'freeze.json') and manifest['plan_sha256']==sha(E/'plan.json')
    reports=[];corner_error=0.;snapshots=0
    for outcome in outcomes:
        request=outcome['request'];file=a.capture/outcome['file'];assert sha(file)==outcome['archive_sha256'] and file.stat().st_size==outcome['archive_bytes']
        logical=gzip.decompress(file.read_bytes());assert len(logical)==outcome['logical_bytes'] and hashlib.sha256(logical).hexdigest()==outcome['logical_sha256']
        d=json.loads(logical);assert d['request']==request and d['outcome']['status']==outcome['status']
        rows=d['rows'];assert len(rows)==outcome['rows']
        report=dict(id=request['id'],stage=request['stage'],mode=request['mode'],target_mps=request.get('target_mps'),location=request['location'],repeat=request['repeat'],status=outcome['status'],collisions=len(d['collisions']))
        manual=request['mode']!='automatic45'
        emergency=False
        for i,row in enumerate(rows):
            assert all(math.isfinite(v) for v in row['location']+row['velocity']+row['rotation']+row['center'])
            corner_error=max(corner_error,body_error(d['body'],row));snapshots+=1
            assert row['phase']==('settle' if i<40 else 'go' if i<100 else 'brake')
            if i:
                assert row['frame']==rows[i-1]['frame']+1 and abs(row['timestamp']-rows[i-1]['timestamp']-.05)<2e-6
            expected_throttle,expected_brake=0.,1.
            if 40<=i<100:
                if request['stage']=='startup':
                    expected_throttle,expected_brake=(.8 if request['mode']=='manual80' else .45),0.
                else:
                    speed=math.hypot(*rows[i-1]['velocity'][:2]);target=request['target_mps']
                    emergency=emergency or speed>1.5
                    if not emergency:
                        expected_throttle=.8 if speed<target else 0.
                        expected_brake=min(.4,max(0.,.4*(speed-target))) if speed>target+.05 else 0.
            for c in (row['requested'],row['actual']):
                assert abs(c['throttle']-expected_throttle)<1e-6 and abs(c['brake']-expected_brake)<1e-6
                assert abs(c['steer'])<1e-9 and not c['hand_brake'] and not c['reverse'] and c['manual_gear_shift']==manual
                if manual:
                    assert c['gear']==1
            assert row['command_wall_ns']>=0 and row['tick_wall_ns']>0
        if outcome['status'] in ('captured','refused'):
            assert len(rows)==180 and d['initial']==rows[39] and d['go_end']==rows[99]
            if emergency:
                assert outcome['status']=='refused' and outcome['reason']=='speed_limit_exceeded'
            else:
                assert outcome['status']=='captured'
            initial,end,brakes=rows[39],rows[99],rows[100:]
            yaw=math.radians(spawns[request['location']]['rotation'][1]);forward=[math.cos(yaw),math.sin(yaw)]
            projection=lambda state:sum((state['center'][k]-initial['center'][k])*forward[k] for k in (0,1))
            index=stop_index(brakes)
            first=(brakes[index]['frame']-end['frame'])*50000 if index is not None else None
            confirmation=(brakes[index+2]['frame']-end['frame'])*50000 if index is not None else None
            prefix=([end]+brakes[:index+3]) if index is not None else [end]+brakes
            body_radius=max(distance(vertex,end['center']) for state in prefix for vertex in state['body_vertices'])
            center_excursion=max(distance(state['center'],end['center']) for state in prefix)
            report.update(forward_go_m=round(projection(end),9),forward_final_m=round(projection(rows[-1]),9),peak_speed_mps=round(max(math.hypot(*r['velocity'][:2]) for r in rows[40:]),9),go_end_speed_mps=round(math.hypot(*end['velocity'][:2]),9),final_speed_mps=round(math.hypot(*rows[-1]['velocity'][:2]),9),first_stop_us=first,confirmed_stop_us=confirmation,command_plus_first_stop_us=50000+first if first is not None else None,command_plus_confirmed_stop_us=50000+confirmation if confirmation is not None else None,command_stop_within_220ms=first is not None and 50000+first<=220000,command_confirmed_within_220ms=confirmation is not None and 50000+confirmation<=220000,command_confirmed_within_500ms=confirmation is not None and 50000+confirmation<=500000,stop_center_excursion_3d_m=round(center_excursion,9),stop_body_enclosure_3d_m=round(body_radius,9),useful_motion=projection(rows[-1])>.5 and len(d['collisions'])==0)
        reports.append(report)
    groups=[]
    for stage in ('startup','feedback'):
        keys=sorted({(r['mode'],r['target_mps']) for r in reports if r['stage']==stage},key=str)
        for mode,target in keys:
            allrows=[r for r in reports if r['stage']==stage and r['mode']==mode and r['target_mps']==target]
            captured=[r for r in allrows if r['status']=='captured']
            g=dict(stage=stage,mode=mode,target_mps=target,planned=len(allrows),captured=len(captured),failed_or_refused=len(allrows)-len(captured),collisions=sum(r['collisions'] for r in allrows))
            if captured:
                g.update(median_final_progress_m=round(median([r['forward_final_m'] for r in captured]),9),median_peak_speed_mps=round(median([r['peak_speed_mps'] for r in captured]),9),useful_motion=sum(r['useful_motion'] for r in captured),command_stop_within_220ms=sum(r['command_stop_within_220ms'] for r in captured),command_confirmed_within_220ms=sum(r['command_confirmed_within_220ms'] for r in captured),command_confirmed_within_500ms=sum(r['command_confirmed_within_500ms'] for r in captured),max_command_confirmed_stop_us=max((r['command_plus_confirmed_stop_us'] for r in captured if r['command_plus_confirmed_stop_us'] is not None),default=None),max_stop_center_excursion_3d_m=max(r['stop_center_excursion_3d_m'] for r in captured),max_stop_body_enclosure_3d_m=max(r['stop_body_enclosure_3d_m'] for r in captured))
            groups.append(g)
    result=dict(planned=36,captured=sum(r['status']=='captured' for r in reports),snapshots=snapshots,max_body_reconstruction_error_m=round(corner_error,9),episodes=reports,groups=groups,freeze_sha256=sha(E/'freeze.json'),outcomes_sha256=sha(a.capture/'outcomes.json'),validation='passed',scope='Independent finite sampled physical realization; no continuous actuation bound, scene risk certification, evidence-guided control or radio result.',goal_complete=False)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(dict(validation='passed',planned=36,snapshots=snapshots,groups=groups),sort_keys=True),flush=True)


if __name__=='__main__':
    main()
