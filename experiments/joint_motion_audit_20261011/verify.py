"""Independent elimination of p/v bands, packet/source/fee audit.

Does not import or call the production polygon inference or expiry solver.
Written as an audit supplement; it does not change frozen experiment choices.
"""
import argparse
import gzip
import hashlib
import json
import zlib
from fractions import Fraction as F
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def axis_extrema(history, axis):
    source = history[-1][0]
    lower, upper = [], []
    for stamp, bounds in history:
        dt = F(source-stamp, 1000000)
        pad = 1500000*dt*dt
        lower.append((F(bounds[axis][0])-pad, dt))
        upper.append((F(bounds[axis][1])+pad, dt))
    vlo, vhi = F(-5000000), F(5000000)
    # Eliminate p: every lower affine line must be below every upper line.
    for lo, dl in lower:
        for hi, du in upper:
            a, b = du-dl, lo-hi
            if a == 0:
                if b > 0:
                    return None
            elif a > 0:
                vlo = max(vlo, b/a)
            else:
                vhi = min(vhi, b/a)
    if vlo > vhi:
        return None
    plo = max(lo+d*vlo for lo, d in lower)
    phi = min(hi+d*vhi for hi, d in upper)
    return plo, phi, vlo, vhi


def independent_expiry(history, query, radius):
    if any(bounds is None for stamp, bounds in history):
        return 0
    extrema = [axis_extrema(history, a) for a in (0, 1)]
    if any(e is None for e in extrema):
        return 0
    candidates = []
    for (lo, hi, vlo, vhi), q in zip(extrema, query):
        for gap, speed in ((lo-q-radius, vlo), (q-hi-radius, -vhi)):
            if gap <= 0:
                candidates.append(0)
                continue
            def safe(t):
                dt = F(t, 1000000)
                return gap+speed*dt-1500000*dt*dt > 0
            # No floating point root rounding or production support function.
            left, right = 0, 500001
            while left+1 < right:
                mid = (left+right)//2
                if safe(mid):
                    left = mid
                else:
                    right = mid
            assert safe(left) and (left == 500000 or not safe(left+1))
            candidates.append(left)
    return max(candidates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    science = json.loads((args.analysis/'scientific.json').read_bytes())
    fees = json.loads((args.analysis/'fees.json').read_bytes())
    outcomes = json.loads((args.capture/'outcomes.json').read_bytes())
    assert science['capture_manifest_sha256'] == sha(args.capture/'manifest.json')
    frozen = Path('experiments/joint_motion_expiry_20261011/freeze.json')
    assert science['freeze_sha256'] == sha(frozen)
    for section in ('sources', 'inputs'):
        for name, digest in json.loads(frozen.read_bytes())[section].items():
            assert sha(Path(name)) == digest
    cloud_count, packet_count, prefix_count = 0, 0, 0
    derived = dict(planned=len(outcomes), captured=0, sources=0, queries=0,
                   current_center_missed=0, history_center_missed=0,
                   source_state_missed=0, sampled_motion_violated=0,
                   empty_current=0, domain_audit_ok=0, methods={})
    for method in ('joint', 'factorized', 'snapshot'):
        derived['methods'][method] = dict(unpaid_allowed=0, paid_allowed=0,
            selected_domain_audit_bad=0, selected_censored=0, selected_uncensored_sampled_conflicts=0)
    assert len(science['episodes']) == len(outcomes)
    for outcome, episode in zip(outcomes, science['episodes']):
        assert outcome['id'] == episode['id'] and outcome['status'] == episode['status']
        path = args.capture/outcome['file']
        assert sha(path) == outcome['sha256']
        logical = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(logical).hexdigest() == outcome['logical_sha256']
        record = json.loads(logical)
        if outcome['status'] != 'captured':
            assert not episode['sources'] and record.get('exception')
            continue
        derived['captured'] += 1
        assert len(record['sources']) == len(episode['sources']) == 30
        history, free = [], 0
        for source, result in zip(record['sources'], episode['sources']):
            assert source['source_us'] == result['source_us'] and source['step'] == result['step']
            assert sha(args.capture/'clouds'/source['cloud']) == source['cloud_sha256']
            cloud_count += 1
            history.append((source['source_us'], result['bounds_um']))
            history = history[-7:]
            key = episode['id']+'_s%02d' % source['step']
            wirepath = args.analysis/'packets'/(key+'.bin')
            assert sha(wirepath) == result['packet_sha256']
            wire = wirepath.read_bytes()
            data = zlib.decompress(wire)
            assert hashlib.sha256(data[:-32]).digest() == data[-32:]
            packet = json.loads(data[:-32])
            assert packet['source_us'] == source['source_us'] and packet['history'] == [[t, b] for t, b in history]
            assert packet['context'] == sha(Path('experiments/joint_motion_expiry_20261011/context.json'))
            assert packet['action_us'] == 300000 and packet['query_radius_um'] == 2500000
            assert len(wire) == result['wire_bytes']
            paid = fees[key]
            assert paid == {k:result[k] for k in ('source_fee_us', 'receiver_fee_us')}
            begin = max(source['source_us']+source['acquisition_us']+paid['source_fee_us'], free)
            free = begin+(len(wire)*8*1000000+19999999)//20000000
            arrival = free+20000
            use = max(source['source_us']+100000, arrival)+paid['receiver_fee_us']+20000
            assert result['use_us'] == use and result['arrival_us'] == arrival
            packet_count += 1
            derived['sources'] += 1
            for counter, value in [('current_center_missed', not result['current_center_covered']),
                ('history_center_missed', not result['history_center_covered']),
                ('source_state_missed', not result['source_state_covered']),
                ('sampled_motion_violated', not result['sampled_motion_ok']),
                ('empty_current', result['bounds_um'] is None), ('domain_audit_ok', result['domain_audit_ok'])]:
                derived[counter] += int(value)
            for qi, query in enumerate(result['queries']):
                derived['queries'] += 1
                point = query['query_um']
                assert point == packet['queries'][qi]
                radius = science['target_radius_um']+2500000
                expected = independent_expiry(history, point, radius)
                snapshot = independent_expiry(history[-1:], point, radius)
                for method in ('joint', 'factorized', 'snapshot'):
                    value = query['methods'][method]
                    expiry = expected if method != 'snapshot' else snapshot
                    assert value['expiry_us'] == packet['prefixes'][method][qi] == expiry
                    assert value['remaining_us'] == expiry-(use-source['source_us'])-300000
                    paid_allowed = use-source['source_us']+300000 <= expiry
                    unpaid_allowed = 400000 <= expiry
                    assert value['paid_allowed'] == paid_allowed and value['unpaid_allowed'] == unpaid_allowed
                    counts = derived['methods'][method]
                    counts['paid_allowed'] += int(paid_allowed)
                    counts['unpaid_allowed'] += int(unpaid_allowed)
                    if paid_allowed:
                        counts['selected_domain_audit_bad'] += int(not result['domain_audit_ok'])
                        counts['selected_censored'] += int(not value['audit_uncensored'])
                        counts['selected_uncensored_sampled_conflicts'] += int(value['audit_uncensored'] and not value['sampled_prefix_separated'])
                    prefix_count += 1
    assert derived == science['summary'], (derived, science['summary'])
    receipt = dict(status='PASS', independent_method='exact pairwise affine-band elimination',
                   scientific_sha256=sha(args.analysis/'scientific.json'),
                   clouds_verified=cloud_count, packets_verified=packet_count,
                   prefixes_recomputed=prefix_count, summary=derived)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'summary'}, sort_keys=True))


if __name__ == '__main__':
    main()
