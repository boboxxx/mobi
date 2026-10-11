"""Whole-episode physical/expiry audit; this is not a risk certificate."""
import argparse
import gzip
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import runtime as R
from capture import check, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check()
    assert not args.out.exists()
    context = json.loads((Path(__file__).parent/'context.json').read_bytes())
    outcomes = json.loads((args.capture/'outcomes.json').read_bytes())
    plan = json.loads((Path(__file__).parent/'plan.json').read_bytes())
    assert [r['id'] for r in outcomes] == [r['id'] for r in plan]
    reports = []
    for request, outcome in zip(plan, outcomes):
        path = args.capture/outcome['file']
        assert R.sha(path) == outcome['sha256']
        logical = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(logical).hexdigest() == outcome['logical_sha256']
        data = json.loads(logical)
        assert data['request'] == request and data['outcome']['status'] == outcome['status']
        report = dict(id=request['id'], pair=request['pair'], motion=request['motion'], method=request['method'], status=outcome['status'])
        if outcome['status'] != 'captured':
            report['exception'] = data.get('exception')
            reports.append(report)
            continue
        rows, sources = data['rows'], data['sources']
        assert len(rows) == 630 and len(sources) == 300
        positions = [(np.asarray(row['truth']['center'])-context['basis']['anchor'])@np.asarray(context['basis']['road']) for row in rows]
        velocities = [np.asarray(row['truth']['velocity'])@np.asarray(context['basis']['road']) for row in rows]
        centre_misses, state_misses, source_total, free = 0, 0, 0, 0
        history = []
        for source in sources:
            assert R.sha(args.capture/'clouds'/source['cloud']) == source['cloud_sha256']
            packetpath = args.capture/'packets'/source['packet']
            assert R.sha(packetpath) == source['packet_sha256']
            decoded = R.decode(packetpath.read_bytes(), context)
            assert decoded['source_us'] == source['source_us'] and decoded['frame'] == source['frame']
            assert source['source_us'] == rows[source['step']]['now_us']
            begin = max(source['source_us']+source['acquisition_us']+source['source_fee_us'], free)
            free = begin+(source['wire_bytes']*8*1000000+19999999)//20000000
            assert source['arrival_us'] == free+20000 and source['tx_free_us'] == free
            bounds = source['meta']['bounds_um']
            p = [F(float(x))*1000000 for x in positions[source['step']][:2]]
            v = [F(float(x))*1000000 for x in velocities[source['step']][:2]]
            covered = bounds is not None and all(lo <= x <= hi for x, (lo, hi) in zip(p, bounds))
            centre_misses += int(not covered)
            history.append((source['source_us'], bounds))
            history = history[-7:]
            assert decoded['history'] == [[t, b] for t, b in history]
            state = decoded['states']['history']
            source_total += 1
            state_ok = state is not None and all(lo <= pp <= hi and vl <= vv <= vh for (lo, hi, vl, vh), pp, vv in zip(state, p, v))
            if state_ok:
                for t, b in history:
                    d = F(source['source_us']-t, 1000000)
                    state_ok &= all(F(lo)-1500000*d*d-150000*d <= pp-d*vv <= F(hi)+1500000*d*d+150000*d for (lo, hi), pp, vv in zip(b, p, v))
            state_misses += int(not state_ok)
        snapshots = [row['own'] for row in rows]+[rows[-1]['after']]
        max_speed = max(math.hypot(*own['velocity'][:2]) for own in snapshots)
        max_target_speed = max(float(np.linalg.norm(v[:2])) for v in velocities)
        max_target_acceleration = max(float(np.linalg.norm((velocities[i][:2]-velocities[i-1][:2])/((rows[i]['now_us']-rows[i-1]['now_us'])/1000000))) for i in range(1, len(rows)))
        modulus_violations = 0
        max_modulus_excess = 0.
        for i in range(len(rows)):
            for j in range(i+1, min(len(rows), i+21)):
                dt = (rows[j]['now_us']-rows[i]['now_us'])/1000000
                excess = float(np.linalg.norm(velocities[j][:2]-velocities[i][:2]))-3*dt-.15
                modulus_violations += int(excess > 1e-6)
                max_modulus_excess = max(max_modulus_excess, excess)
        progress = [R.own_position(own, context['basis'])[0]/1000000 for own in snapshots]
        policy_errors, expired_grants, shape_misses = 0, 0, 0
        sampled_min_gap = None
        ego_radius = R.A.pose.enclosing_radius_um(data['body']['extent'])
        target_radius = R.A.pose.enclosing_radius_um(context['extent'])
        for i, row in enumerate(rows):
            assert row['own']['frame']+1 == row['after']['frame']
            assert abs(row['after']['timestamp']-row['own']['timestamp']-.05) < 2e-6
            before_refused = (i > 0 and rows[i-1]['episode_refused']) or not row['domain_ok'] or any(e['frame'] <= row['own']['frame'] for e in data['collisions'])
            before_budget = row['receiver_fee_us']+row['query_fee_us'] <= 20000
            expected = i < 600 and not before_refused and not row['reached'] and before_budget and row['gate']['allowed']
            policy_errors += int(bool(expected) != row['engineering_go'])
            # Post-command or post-tick refusal can occur after the issued grant.
            if row['engineering_go']:
                expired_grants += int(row['gate']['source_us'] is None or row['decision_us']+300000 > row['gate']['source_us']+row['gate']['expiry_us'])
                q = np.asarray(row['query_um'], dtype=float)
                for j in range(i, min(len(rows), i+7)):
                    centre = (np.asarray(rows[j]['own']['center'])-context['basis']['anchor'])@np.asarray(context['basis']['road'])
                    shape_misses += int(np.linalg.norm(centre[:2]*1000000-q)+ego_radius > R.RADIUS)
            throttle, brake = R.relay(row['own'], row['engineering_go'])
            policy_errors += int(abs(throttle-row['requested_throttle']) > 1e-9 or abs(brake-row['requested_brake']) > 1e-9)
            actual = row['after']['actual']
            policy_errors += int(abs(actual['throttle']-throttle) > 1e-6 or abs(actual['brake']-brake) > 1e-6 or not actual['manual_gear_shift'] or actual['gear'] != 1)
            ownxy = (np.asarray(row['own']['center'])-context['basis']['anchor'])@np.asarray(context['basis']['road'])
            gap = float(np.linalg.norm(ownxy[:2]-positions[i][:2]))-(ego_radius+target_radius)/1000000
            sampled_min_gap = gap if sampled_min_gap is None else min(sampled_min_gap, gap)
        report.update(sources=source_total, centre_misses=centre_misses, source_state_misses=state_misses,
            selected=sum(row['engineering_go'] for row in rows), goal_reached=any(row['reached'] for row in rows),
            goal_reached_us=next((row['now_us']-rows[0]['now_us'] for row in rows if row['reached']), None),
            episode_refused=any(row['episode_refused'] for row in rows), collisions=len(data['collisions']),
            final_progress_m=progress[-1]-progress[0], max_progress_m=max(progress)-progress[0],
            max_ego_speed_mps=max_speed, max_target_speed_mps=max_target_speed,
            max_sampled_target_acceleration_mps2=max_target_acceleration, sampled_min_body_ball_gap_m=sampled_min_gap,
            sampled_velocity_modulus_violations=modulus_violations, sampled_max_modulus_excess_mps=max_modulus_excess,
            expired_grants=expired_grants, selected_sampled_ego_envelope_misses=shape_misses, policy_reconstruction_errors=policy_errors,
            processing_budget_violations=sum(not row['processing_budget_ok'] for row in rows))
        reports.append(report)
    result = dict(freeze_sha256=R.sha(Path(__file__).parent/'freeze.json'), episodes=reports,
        scope='whole-episode development audit; sample checks not continuous or IID guarantee', goal_complete=False,
        summary=dict(planned=len(plan), captured=sum(e['status']=='captured' for e in reports),
                     collisions=sum(e.get('collisions', 0) for e in reports),
                     source_centre_misses=sum(e.get('centre_misses', 0) for e in reports),
                     source_state_misses=sum(e.get('source_state_misses', 0) for e in reports),
                     methods={m:dict(planned=sum(r['method']==m for r in plan),
                         route_completed=sum(e.get('goal_reached', False) for e in reports if e['method']==m),
                         refused=sum(e.get('episode_refused', False) for e in reports if e['method']==m)) for m in ('history', 'snapshot')}))
    write(args.out, result)
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
