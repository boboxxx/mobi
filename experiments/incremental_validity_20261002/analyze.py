#!/usr/bin/env python3
"""Independent provenance/history/deadline replay; no experimental sender import."""
import argparse, copy, gzip, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/evidence_loop_20261001'))
from fast_path import body, Receiver
sys.path.insert(0, str(ROOT / 'experiments/expiry_frontier_20261001'))
from frontier import frontier

STAGES = ['selected', 'all', 'selected_shared', 'all_shared']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ray_keys(o, r):
    return {tuple(o[x[0]]) + tuple(x[1:]) for x in r}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--selected-capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    stages = {k: json.loads((a.results / k / 'analysis.json').read_bytes()) for k in STAGES}
    profiles = dict(small=body.Profile(r_min=.2, r_max=.4, query_radius=0., step=.05, error=0.),
                    vehicle=body.Profile(r_min=.55, r_max=2.5, query_radius=0., step=.1, error=0.))
    contract = body.Contract()
    contexts, rows = {}, {}
    for k, study in stages.items():
        selected = k.startswith('selected')
        assert study['mode'] == ('selected' if selected else 'all')
        assert (study['states'], len(study['rows'])) == ((6, 162) if selected else (384, 1152))
        contexts[k] = {(c['run'], c['id']): c for c in study['contexts']}
        assert len(contexts[k]) == study['states']
        rows[k] = defaultdict(list)
        for r in study['rows']:
            rows[k][(r['run'], r['id'])].append(r)
        assert set(rows[k]) == set(contexts[k])
        for f, h in study['source_sha256'].items():
            assert not Path(f).name.startswith('._')
            assert sha(ROOT / f) == h, (k, f)
        for f, h in study['input_sha256'].items():
            p = (a.selected_capture / Path(f).relative_to('results/live_repair_closed_loop_20261001/capture')
                 if selected else a.capture / Path(f).relative_to('results/online_evidence_20261002/live'))
            assert sha(p) == h, (k, f)
        protocol = 'SHARED_PROTOCOL.md' if k.endswith('_shared') else 'PROTOCOL.md'
        assert study['protocol_sha256'] == sha(Path(__file__).with_name(protocol))
        build = json.loads((a.results / ('build_shared.json' if k.endswith('_shared') else 'build.json')).read_bytes())
        assert study['library_sha256'] == build['binary_sha256']
        assert build['source_sha256'] == sha(ROOT / 'experiments/usable_lease_20261002/cover.cpp')
    assert contexts['selected'] == contexts['selected_shared']
    assert contexts['all'] == contexts['all_shared']
    assert not (set(contexts['selected']) & set(contexts['all']))
    packet_checks = defaultdict(int)
    frontier_checks = 0
    matched_packets = defaultdict(int)
    negative_geometry_rows = defaultdict(int)
    audited_timing_rows = 0
    for name in sorted({key[0] for key in set(contexts['all']) | set(contexts['selected'])}):
        selected_run = name in {key[0] for key in contexts['selected']}
        run = (a.selected_capture if selected_run else a.capture) / name
        record = json.loads(gzip.decompress((run / 'record.json.gz').read_bytes()))
        rx = Receiver(profiles, contract, name, 'Carla/Maps/Town10HD_Opt')
        template = None
        for d in record['decisions']:
            key = (name, d['id'])
            old = (run / 'packets' / (d['id'] + '.json')).read_bytes() if d['geometry'] else None
            motion = body.Motion(half_length=2.3, half_width=1.3, yaw=d['yaw'], acceleration=0., yaw_rate=0.)
            prior = rx.latest_region()
            if prior and not (prior.established <= d['stamp'] and math.ceil(d['stamp'] * 1e6) < rx._deadlines[prior.identity]):
                prior = None
            assert (prior.identity if prior else None) == d['prior']
            plane = json.loads(old)['raw']['payload']['scope']['plane_z'] if old else 0.
            scope = body.Scope(name, rx.frame_id, tuple(d['query']), plane)
            if key in contexts['all'] or key in contexts['selected']:
                with np.load(run / 'clouds' / (d['id'] + '.npz')) as cloud:
                    encoded = body.encode_source(cloud['xyz'], cloud['origin'], d['stamp'], d['stamp'])
                    scope = body.Scope(name, rx.frame_id, tuple(d['query']), float(cloud['plane_z']))
                original_rays = ray_keys(encoded[0], encoded[1])
            full_h = None
            if key in contexts['selected']:
                full_h = frontier(body.projections(*encoded, profiles, scope, contract), profiles,
                                  scope, motion, prior, encoded[2] / 1e6, 1_000_000)['horizon_us']
            for stage, study in stages.items():
                if key not in contexts[stage]:
                    continue
                c = contexts[stage][key]
                assert c['decision'] == d
                assert body.canonical(c['prior']) == body.canonical(body.asdict(prior) if prior else None)
                assert c['template_sha256'] == (hashlib.sha256(template).hexdigest() if template else None)
                assert c['full_input_horizon_us'] == (full_h if stage.startswith('selected') else None)
                group = rows[stage][key]
                assert len(group) == (27 if stage.startswith('selected') else 3)
                seen = set()
                for r in group:
                    signature = (r['method'], r['repeat'], r['horizon_ms'])
                    assert signature not in seen
                    seen.add(signature)
                    assert r['method'] in ['old', 'nearest', 'gap_greedy']
                    assert sorted(r['order']) == ['gap_greedy', 'nearest', 'old']
                    h_us = math.floor(r['horizon_ms'] * 1000)
                    assert r['acquisition_ms'] == float(d['acquisition_s']) * 1000
                    assert r['wire_ms'] == 20 + r['packet_bytes'] * 8 / 20_000
                    assert r['original_wire_ms'] == (20 if record.get('link_mbps') == 0 else r['wire_ms'])
                    assert r['generation_ms'] >= 0 and r['verification_ms'] >= 0
                    cost_ms = sum(r[x] for x in ['acquisition_ms', 'generation_ms', 'verification_ms', 'wire_ms'])
                    ticks = max(50_000, math.ceil(cost_ms / 50) * 50_000)
                    assert r['tick_age_us'] == ticks
                    assert r['usable_us'] == (h_us - math.ceil(cost_ms * 1000) if r['geometry'] else None)
                    assert r['action_slack_us'] == (h_us - ticks - 200_000 if r['geometry'] else None)
                    assert r['hypothetical_action_pass'] == bool(r['geometry'] and r['hypothetical_temporal_accept'] and ticks + 200_000 < h_us)
                    original_ticks = max(50_000, math.ceil(sum(r[x] for x in ['acquisition_ms', 'generation_ms', 'verification_ms', 'original_wire_ms']) / 50) * 50_000)
                    assert r['original_link_action_pass'] == bool(r['geometry'] and original_ticks + 200_000 < h_us)
                    audited_timing_rows += 1
                    if not r['geometry']:
                        negative_geometry_rows[stage] += 1
                        assert r['packet_bytes'] == 0 and r['rays'] == 0 and not r['hypothetical_temporal_accept']
                        continue
                    # Only the first repeat's bytes were archived; other repeats
                    # are arithmetic audited, not independently packet reverified.
                    if r['repeat'] != 0:
                        continue
                    filename = name + '_' + d['id'] + '_' + r['method'] + '_' + str(round(r['horizon_ms'])) + '.json'
                    blob = (a.results / stage / 'packets' / filename).read_bytes()
                    assert len(blob) == r['packet_bytes']
                    assert copy.deepcopy(rx).accept(blob, scope, motion, d['stamp'] + .02)
                    p, o, rays = body.decode(body.canonical(json.loads(blob)['raw']), profiles, scope, contract)
                    assert p['reference_us'] == encoded[2] and p['sequence'] == d['sequence'] and p['horizon_us'] == h_us
                    assert len(rays) == r['rays'] and ray_keys(o, rays) <= original_rays
                    late_accept = copy.deepcopy(rx).accept(blob, scope, motion, (encoded[2] + ticks) / 1e6)
                    assert late_accept == r['hypothetical_temporal_accept']
                    if stage.startswith('selected'):
                        subset_h = frontier(body.projections(o, rays, encoded[2], profiles, scope, contract),
                                            profiles, scope, motion, prior, encoded[2] / 1e6, 1_000_000)['horizon_us']
                        assert r['subset_frontier_us'] == subset_h and h_us <= subset_h <= full_h
                        frontier_checks += 1
                    packet_checks[stage] += 1
                    if stage.endswith('_shared'):
                        assert blob == (a.results / stage[:-len('_shared')] / 'packets' / filename).read_bytes()
                        matched_packets[stage] += 1
            if old:
                template = old
            if d['receiver_accepted']:
                assert rx.accept(old, scope, motion, d['receiver_check_time'])
    summaries, paired = [], []
    for stage, study in stages.items():
        groups = defaultdict(list)
        for r in study['rows']:
            groups[(r['run'], r['id'], r['method'], r['horizon_ms'])].append(r)
        for key, g in sorted(groups.items()):
            assert len(g) == (3 if stage.startswith('selected') else 1)
            assert len({r['geometry'] for r in g}) == 1
            x = dict(stage=stage, run=key[0], id=key[1], method=key[2], horizon_ms=key[3],
                     geometry=g[0]['geometry'], fallbacks=sum(r['used_fallback'] for r in g),
                     action_passes=sum(r['hypothetical_action_pass'] for r in g),
                     original_link_action_passes=sum(r['original_link_action_pass'] for r in g),
                     repair_diagnostics=g[0]['repair_diagnostics'])
            for f in ['generation_ms', 'verification_ms', 'packet_bytes', 'rays', 'wire_ms', 'usable_us', 'action_slack_us']:
                x[f + '_median'] = float(np.median([r[f] for r in g])) if g[0][f] is not None else None
            summaries.append(x)
    for original, shared in [('selected', 'selected_shared'), ('all', 'all_shared')]:
        left = {(r['run'], r['id'], r['method'], r['horizon_ms'], r['repeat']): r for r in stages[original]['rows']}
        right = {(r['run'], r['id'], r['method'], r['horizon_ms'], r['repeat']): r for r in stages[shared]['rows']}
        assert set(left) == set(right)
        for key in left:
            l, r = left[key], right[key]
            for f in ['geometry', 'used_fallback', 'repair_diagnostics', 'packet_bytes', 'rays', 'subset_frontier_us', 'order']:
                assert l[f] == r[f], (key, f)
        for method in ['old', 'nearest', 'gap_greedy']:
            pairs = [(left[k], right[k]) for k in left if k[2] == method]
            paired.append(dict(original=original, shared=shared, method=method,
                               geometry=sum(l['geometry'] for l, r in pairs),
                               original_action=sum(l['hypothetical_action_pass'] for l, r in pairs),
                               shared_action=sum(r['hypothetical_action_pass'] for l, r in pairs),
                               gained=sum(not l['hypothetical_action_pass'] and r['hypothetical_action_pass'] for l, r in pairs),
                               lost=sum(l['hypothetical_action_pass'] and not r['hypothetical_action_pass'] for l, r in pairs)))
    result = dict(packet_checks=dict(packet_checks), frontier_checks=frontier_checks,
                  byte_matches=dict(matched_packets), arithmetic_rows=audited_timing_rows,
                  negative_geometry_rows=dict(negative_geometry_rows), summaries=summaries, paired_shared=paired,
                  analyzer_sha256=sha(Path(__file__)),
                  scope='Independent first-repeat packet/history/source/full-receiver replay; all row arithmetic checked. Shared outputs identical. Observed retrospective timing, no counterfactual trajectory or WCET claim.')
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['packet_checks', 'frontier_checks', 'byte_matches', 'arithmetic_rows', 'negative_geometry_rows', 'paired_shared']}))


if __name__ == '__main__':
    main()
