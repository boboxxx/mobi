"""Independent queue/admission reconstruction plus full physical sample audit."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from fractions import Fraction as F
import numpy as np
import model as M
R=M.R

parser=argparse.ArgumentParser()
parser.add_argument('--capture',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
assert not args.out.exists()
E=Path(__file__).parent
freeze=json.loads((E/'freeze.json').read_bytes())
for section in ('sources','inputs'):
    for name,digest in freeze[section].items(): assert R.sha(R.ROOT/name)==digest,name
plan=json.loads((E/'plan.json').read_bytes())
context=json.loads((E/'context.json').read_bytes())
outcomes=json.loads((args.capture/'outcomes.json').read_bytes())
assert [r['id'] for r in plan]==[o['id'] for o in outcomes]
ctxhash=hashlib.sha256(R.canonical(context)).hexdigest()
target_radius=R.A.pose.enclosing_radius_um(context['extent'])
reports=[]
for request,outcome in zip(plan,outcomes):
    path=args.capture/outcome['file']; assert R.sha(path)==outcome['sha256']
    raw=gzip.decompress(path.read_bytes()); assert hashlib.sha256(raw).hexdigest()==outcome['logical_sha256']
    d=json.loads(raw); assert d['request']==request
    report=dict(id=request['id'],method=request['method'],motion=request['motion'],pair=request['pair'],status=outcome['status'])
    if outcome['status']!='captured':
        report['exception']=d.get('exception');reports.append(report);continue
    rows,sources,controls=d['rows'],d['sources'],d['controls']
    assert len(rows)==630 and len(sources)==300
    basis=context['basis']; anchor=np.asarray(basis['anchor']); road=np.asarray(basis['road'])
    positions=[(np.asarray(row['truth']['center'])-anchor)@road for row in rows]
    velocities=[np.asarray(row['truth']['velocity'])@road for row in rows]
    centre_misses=state_misses=0
    cpu=tx=decode=0
    decoded_sources={}
    for source in sources:
        assert source['source_us']==source['step']*50000
        assert source['frame']==rows[source['step']]['own']['frame']
        assert R.sha(args.capture/'clouds'/source['cloud'])==source['cloud_sha256']
        pp=args.capture/'packets'/source['packet']; assert R.sha(pp)==source['packet_sha256']
        obj=R.decode(pp.read_bytes(),context); decoded_sources[source['source_us']]=obj
        assert obj['source_us']==source['source_us'] and obj['frame']==source['frame']
        cpu=max(source['source_us']+50000,cpu)+source['source_fee_us']
        tx=max(cpu,tx)+(source['wire_bytes']*8*1000000+19999999)//20000000
        assert source['source_ready_us']==cpu and source['tx_free_us']==tx and source['arrival_us']==tx+20000
        if 'receiver_fee_us' in source:
            decode=max(tx+20000,decode)+source['receiver_fee_us'];assert source['receiver_ready_us']==decode
        else:assert source['arrival_us']>rows[-1]['now_us']
        p=[F(float(x))*1000000 for x in positions[source['step']][:2]]
        v=[F(float(x))*1000000 for x in velocities[source['step']][:2]]
        bounds=source['meta']['bounds_um']; state=obj['states']['history']
        centre_misses+=int(bounds is None or not all(lo<=x<=hi for x,(lo,hi) in zip(p,bounds or [])))
        state_misses+=int(state is None or not all(lo<=x<=hi and vl<=vv<=vh for (lo,hi,vl,vh),x,vv in zip(state or [],p,v)))
        assert R.extrema(obj['history'])==state
    cpu=tx=decode=0; decoded_controls=[]
    for control in controls:
        pp=args.capture/'packets'/control['packet'];assert R.sha(pp)==control['packet_sha256']
        lease=M.unpack(pp.read_bytes());assert lease==control['lease']
        step=control['step'];stamp=step*50000
        assert lease['episode']==request['id'] and lease['context']==ctxhash
        assert lease['seq']==step and lease['controller_sample_us']==stamp and control['query_us']==stamp
        assert lease['query_um']==rows[step]['query_um']
        eligible=[s for s in sources if s.get('receiver_ready_us',float('inf'))<=stamp]
        assert eligible and eligible[-1]['source_us']==lease['source_us']
        state=decoded_sources[lease['source_us']]['states'][request['method']]
        assert lease['expiry_us']==M.fast_expiry.expiry(state,lease['query_um'],target_radius,request['method'])
        cpu=max(stamp,cpu)+control['query_fee_us'];tx=max(cpu,tx)+(control['wire_bytes']*8*1000000+19999999)//20000000
        assert control['controller_ready_us']==cpu and control['tx_free_us']==tx and control['arrival_us']==tx+20000
        if 'decode_fee_us' in control:
            decode=max(tx+20000,decode)+control['decode_fee_us'];assert control['decode_ready_us']==decode
            decoded_controls.append((decode,lease))
        else:assert control['arrival_us']>rows[-1]['now_us']
    body_radius=R.A.pose.enclosing_radius_um(d['body']['extent'])
    slack=2500000-body_radius-20000-225000
    errors=expired=scope_misses=future_body_misses=future_target_misses=0
    denied={};active=None;index=0
    for i,row in enumerate(rows):
        now=i*50000;assert row['step']==i and row['now_us']==row['decision_us']==now
        assert row['own']['frame']+1==row['after']['frame']
        assert abs(row['own']['timestamp']-d['clock']['base_simulator_timestamp']-now/1000000)<5e-6
        while index<len(decoded_controls) and decoded_controls[index][0]<=now:
            active=decoded_controls[index][1];index+=1
        assert active==row['active_lease']
        position=R.own_position(row['own'],basis);assert position==row['query_um']
        ttl_ok=active is not None and 0<=active['source_us']<=active['controller_sample_us']<=now and now+300000<=active['source_us']+active['expiry_us']
        spatial=active is not None and slack>=0 and sum((a-b)**2 for a,b in zip(active['query_um'],position))<=slack*slack
        allowed=bool(ttl_ok and spatial);errors+=int(allowed!=row['gate']['allowed'])
        domain=math.hypot(*row['own']['velocity'][:2])<=.75 and -10000000<=position[0]<=6000000 and abs(position[1])<=500000
        previous_refused=(i>0 and rows[i-1]['episode_refused']) or not domain or any(e['frame']<=row['own']['frame'] for e in d['collisions'])
        reached=position[0]>=3000000 or (i>0 and rows[i-1]['reached'])
        expected=bool(i<600 and not previous_refused and not reached and allowed)
        errors+=int(expected!=row['engineering_go'])
        throttle,brake=R.relay(row['own'],expected)
        actual=row['after']['actual']
        errors+=int(abs(actual['throttle']-throttle)>1e-6 or abs(actual['brake']-brake)>1e-6 or not actual['manual_gear_shift'] or actual['gear']!=1)
        if not allowed:denied[row['gate']['reason']]=denied.get(row['gate']['reason'],0)+1
        if expected:
            expired+=int(not ttl_ok);scope_misses+=int(not spatial)
            q=np.asarray(active['query_um'],dtype=float)
            for j in range(i,min(i+7,len(rows))):
                bodycentre=(np.asarray(rows[j]['own']['center'])-anchor)@road
                future_body_misses+=int(np.linalg.norm(bodycentre[:2]*1000000-q)+body_radius>2500000)
                future_target_misses+=int(np.linalg.norm(positions[j][:2]*1000000-q)<=2500000+target_radius)
    samples=[r['own'] for r in rows]+[rows[-1]['after']]
    speeds=[math.hypot(*s['velocity'][:2]) for s in samples]
    brake_complete=brake_interrupted=brake_failures=0; confirmations=[]
    for i in range(1,len(rows)):
        if rows[i]['engineering_go'] or not rows[i-1]['engineering_go']:continue
        stop=next((j for j in range(i,len(rows)) if rows[j]['engineering_go']),len(rows))
        confirm=next((j for j in range(i+2,min(stop+1,len(samples))) if all(speeds[k]<=.02 for k in range(j-2,j+1))),None)
        if confirm is not None:
            brake_complete+=1;confirmations.append((confirm-i)*50000)
            brake_failures+=int((confirm-i)*50000>250000)
        elif stop-i>=5:
            brake_failures+=1
        else:brake_interrupted+=1
    modulus_misses=0
    for i in range(len(rows)):
        for j in range(i+1,min(i+21,len(rows))):
            modulus_misses+=int(np.linalg.norm(velocities[j][:2]-velocities[i][:2])>3*(j-i)*.05+.15+1e-6)
    progress=[R.own_position(s,basis)[0]/1000000 for s in samples]
    report.update(sources=len(sources),controls=len(controls),selected=sum(r['engineering_go'] for r in rows),
        goal_reached=any(r['reached'] for r in rows),max_progress_m=max(progress)-progress[0],
        episode_refused=any(r['episode_refused'] for r in rows),collisions=len(d['collisions']),
        centre_misses=centre_misses,state_misses=state_misses,policy_errors=errors,expired_grants=expired,
        scope_misses=scope_misses,future_sampled_body_misses=future_body_misses,future_sampled_target_misses=future_target_misses,
        max_ego_speed_mps=max(speeds),max_target_speed_mps=max(float(np.linalg.norm(v[:2])) for v in velocities),
        sampled_modulus_violations=modulus_misses,brake_complete=brake_complete,brake_interrupted=brake_interrupted,
        brake_confirmation_failures=brake_failures,max_brake_confirmation_us=max(confirmations) if confirmations else None,
        admission_denials=denied)
    reports.append(report)
result=dict(scope='12 fixed development episodes with virtual event clock; conditional sample audit, no wallclock or IID certificate',
    freeze_sha256=R.sha(E/'freeze.json'),episodes=reports,goal_complete=False,
    summary=dict(planned=len(plan),captured=sum(e['status']=='captured' for e in reports),
        collisions=sum(e.get('collisions',0) for e in reports),policy_errors=sum(e.get('policy_errors',0) for e in reports),
        methods={method:dict(planned=sum(p['method']==method for p in plan),
            clear_route_completed=sum(e.get('goal_reached',False) for e in reports if e['method']==method and e['motion']!='approach_stop'),
            all_route_completed=sum(e.get('goal_reached',False) for e in reports if e['method']==method)) for method in ('history','snapshot')}))
args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result['summary'],sort_keys=True))
