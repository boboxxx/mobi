"""Paired XYZ-only reference, paid shadow queries, separate truth auditing."""
import argparse
import gzip
import hashlib
import json
import math
import time
import zlib
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import adapter as A
import observer as O
from capture import check, dump, sha

E = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def audit_state(row, basis):
    # Truth is deliberately isolated from inference and encoding APIs.
    position = (np.asarray(row['truth']['center'])-basis['anchor'])@np.asarray(basis['road'])
    velocity = np.asarray(row['truth']['velocity'])@np.asarray(basis['road'])
    return position[:2], velocity[:2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--fees-from', type=Path)
    args = ap.parse_args()
    check()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'packets').mkdir()
    ctx = json.loads((E/'context.json').read_bytes())
    background = json.loads((A.ROOT/'results/background_frontend_20261004/background.json').read_bytes())
    outcomes = json.loads((args.capture/'outcomes.json').read_bytes())
    saved_fees = json.loads(args.fees_from.read_bytes()) if args.fees_from else None
    methods = ('joint', 'factorized', 'snapshot')
    queries = ((-6000000, 0), (-4000000, 0))
    radius = A.pose.enclosing_radius_um(ctx['extent'])
    context_digest = sha(E/'context.json')
    episodes, fees, timings = [], {}, {}
    start_all = time.perf_counter()
    for outcome in outcomes:
        path = args.capture/outcome['file']
        assert sha(path) == outcome['sha256']
        record = json.loads(gzip.decompress(path.read_bytes()))
        entry = dict(id=outcome['id'], status=outcome['status'], motion=record['request']['motion'], sources=[])
        if outcome['status'] != 'captured':
            episodes.append(entry)
            continue
        history, source_truth_coverage = [], []
        free = 0
        rows = record['rows']
        assert len(rows) == 60 and len(record['sources']) == 30
        truth = [audit_state(row, ctx['basis']) for row in rows]
        for source in record['sources']:
            path = args.capture/'clouds'/source['cloud']
            assert sha(path) == source['cloud_sha256']
            with np.load(path) as cloud:
                raw, transform = cloud['raw'].copy(), cloud['transform'].copy()
            step, stamp = source['step'], source['source_us']
            key = entry['id']+'_s%02d' % step
            start = time.perf_counter_ns()
            xyz = np.c_[raw['x'], raw['y'], raw['z']].astype('<f4')
            bounds, geometry = A.center_bounds(xyz, transform, ctx['extent'], ctx['basis'], background)
            history.append((stamp, bounds))
            joint = O.infer(history)
            polygons = dict(joint=joint, factorized=O.factorize(joint), snapshot=O.infer(history[-1:]))
            prefixes = {method: [O.expiry(polygons[method], query, radius) for query in queries] for method in methods}
            assert prefixes['joint'] == prefixes['factorized'], 'future support identity failed'
            packet = dict(version=1, source_us=stamp, context=context_digest, blueprint=ctx['blueprint'],
                          queries=list(queries), action_us=O.ACTION, query_radius_um=O.QUERY_RADIUS,
                          history=history[-O.HISTORY:], prefixes=prefixes)
            data = canonical(packet)
            wire = zlib.compress(data+hashlib.sha256(data).digest(), 6)
            computed_source_fee = (time.perf_counter_ns()-start+999)//1000+source['copy_us']
            start = time.perf_counter_ns()
            decoded = zlib.decompress(wire)
            assert hashlib.sha256(decoded[:-32]).digest() == decoded[-32:]
            obj = json.loads(decoded[:-32])
            assert obj['source_us'] == stamp and obj['context'] == context_digest
            assert obj['action_us'] == O.ACTION and obj['queries'] == [list(q) for q in queries]
            computed_receiver_fee = (time.perf_counter_ns()-start+999)//1000
            measured = dict(source_fee_us=computed_source_fee, receiver_fee_us=computed_receiver_fee)
            timings[key] = measured
            paid = saved_fees[key] if saved_fees is not None else measured
            fees[key] = paid
            packet_path = args.out/'packets'/(key+'.bin')
            packet_path.write_bytes(wire)
            tx_begin = max(stamp+source['acquisition_us']+paid['source_fee_us'], free)
            free = tx_begin+(len(wire)*8*1000000+20000000-1)//20000000
            arrival = free+20000
            use = max(stamp+100000, arrival)+paid['receiver_fee_us']+20000
            # Everything below is independent audit; no value returns to inference.
            p, v = truth[step]
            p_exact = [F(float(x))*1000000 for x in p]
            v_exact = [F(float(x))*1000000 for x in v]
            covered = bounds is not None and all(lo <= x <= hi for x, (lo, hi) in zip(p_exact, bounds))
            source_truth_coverage.append(bool(covered))
            history_covered = all(source_truth_coverage[-O.HISTORY:])
            state_covered = O.contains(joint, p_exact, v_exact)
            max_speed = 0.
            max_accel_axis = 0.
            first_step = max(0, step-2*(O.HISTORY-1))
            last_step = min(59, step+10)
            for index in range(first_step, last_step+1):
                max_speed = max(max_speed, float(np.linalg.norm(truth[index][1])))
                if index > first_step:
                    dt = (rows[index]['source_us']-rows[index-1]['source_us'])/1000000
                    max_accel_axis = max(max_accel_axis, float(np.max(np.abs(truth[index][1]-truth[index-1][1]))/dt))
            tilt_ok = all(math.hypot(rows[i]['truth']['rotation'][0], rows[i]['truth']['rotation'][2]) <= 5
                          for i in range(first_step, last_step+1))
            motion_sampled_ok = max_speed <= 5 and max_accel_axis <= 3 and tilt_ok
            domain_audit_ok = history_covered and state_covered and motion_sampled_ok
            item = dict(step=step, source_us=stamp, bounds_um=bounds, geometry=geometry,
                        current_center_covered=bool(covered), history_center_covered=history_covered,
                        source_state_covered=bool(state_covered), sampled_motion_ok=bool(motion_sampled_ok),
                        sampled_max_speed_mps=max_speed, sampled_max_accel_axis_mps2=max_accel_axis,
                        domain_audit_ok=bool(domain_audit_ok), source_fee_us=paid['source_fee_us'],
                        receiver_fee_us=paid['receiver_fee_us'], wire_bytes=len(wire),
                        packet_sha256=sha(packet_path), acquisition_us=source['acquisition_us'],
                        arrival_us=arrival, use_us=use, actual_paid_age_us=use-stamp,
                        target_returns_audit_only=source['target_returns_audit_only'], queries=[])
            for qi, query in enumerate(queries):
                results = {}
                for method in methods:
                    expiry = prefixes[method][qi]
                    allowed = O.permit(stamp, expiry, use)
                    uncensored = rows[-1]['source_us'] >= stamp+expiry
                    samples = [i for i, row in enumerate(rows) if stamp <= row['source_us'] <= stamp+expiry]
                    minimum = min((float(np.linalg.norm(truth[i][0]*1000000-np.asarray(query)))-radius-O.QUERY_RADIUS
                                   for i in samples), default=None)
                    results[method] = dict(expiry_us=expiry, remaining_us=expiry-(use-stamp)-O.ACTION,
                        unpaid_allowed=O.permit(stamp, expiry, stamp+100000), paid_allowed=bool(allowed),
                        audit_uncensored=bool(uncensored), sampled_prefix_min_gap_um=minimum,
                        sampled_prefix_separated=minimum is not None and minimum > 0)
                item['queries'].append(dict(query_um=list(query), methods=results))
            entry['sources'].append(item)
        episodes.append(entry)
        print(json.dumps(dict(id=entry['id'], sources=len(entry['sources']), elapsed_s=time.perf_counter()-start_all)), flush=True)
    all_sources = [s for ep in episodes for s in ep['sources']]
    summary = dict(planned=len(outcomes), captured=sum(ep['status']=='captured' for ep in episodes),
                   sources=len(all_sources), queries=sum(len(s['queries']) for s in all_sources),
                   current_center_missed=sum(not s['current_center_covered'] for s in all_sources),
                   history_center_missed=sum(not s['history_center_covered'] for s in all_sources),
                   source_state_missed=sum(not s['source_state_covered'] for s in all_sources),
                   sampled_motion_violated=sum(not s['sampled_motion_ok'] for s in all_sources),
                   empty_current=sum(s['bounds_um'] is None for s in all_sources),
                   domain_audit_ok=sum(s['domain_audit_ok'] for s in all_sources), methods={})
    for method in methods:
        pairs = [(s, q['methods'][method]) for s in all_sources for q in s['queries']]
        selected = [(s, q) for s, q in pairs if q['paid_allowed']]
        summary['methods'][method] = dict(unpaid_allowed=sum(q['unpaid_allowed'] for s, q in pairs),
            paid_allowed=len(selected), selected_domain_audit_bad=sum(not s['domain_audit_ok'] for s, q in selected),
            selected_censored=sum(not q['audit_uncensored'] for s, q in selected),
            selected_uncensored_sampled_conflicts=sum(q['audit_uncensored'] and not q['sampled_prefix_separated'] for s, q in selected))
    science = dict(freeze_sha256=sha(E/'freeze.json'), capture_manifest_sha256=sha(args.capture/'manifest.json'),
                   target_radius_um=radius, scope='known-walker development, conditional geometry, sampled audit only',
                   goal_complete=False, summary=summary, episodes=episodes)
    dump(args.out/'scientific.json', science)
    dump(args.out/'fees.json', fees)
    dump(args.out/'timing.json', dict(replayed_fees=args.fees_from is not None, measured=timings,
                                    elapsed_s=time.perf_counter()-start_all))
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
