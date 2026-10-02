#!/usr/bin/env python3
"""Independent original-input replay and charged horizon-menu accounting."""
import argparse, gzip, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from thin import body
from fast_path import Receiver
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'expiry_frontier_20261001'))
from frontier import frontier as reference_frontier


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    profiles = dict(small=body.Profile(r_min=.2, r_max=.4, query_radius=0., step=.05, error=0.),
                    vehicle=body.Profile(r_min=.55, r_max=2.5, query_radius=0., step=.1, error=0.))
    contract = body.Contract()
    stages = {k: json.loads((a.results / k / 'analysis.json').read_bytes())
              for k in ['matched', 'native']}
    original = {}
    for context in stages['matched']['contexts']:
        original[(context['run'], context['id'])] = context
    for stage in stages.values():
        assert len(stage['rows']) == 288 and len(stage['contexts']) == 6
        for f, h in stage['input_sha256'].items():
            # Saved source paths are server-relative; the explicit capture flag
            # identifies the same corpus when replayed on a different machine.
            p = a.capture / Path(f).relative_to('results/live_repair_closed_loop_20261001/capture')
            assert hashlib.sha256(p.read_bytes()).hexdigest() == h, f
        for f, h in stage['source_sha256'].items():
            p = (a.results / 'archived_metadata' / f if Path(f).name.startswith('._')
                 else Path(f))
            assert hashlib.sha256(p.read_bytes()).hexdigest() == h, f
        for context in stage['contexts']:
            assert context == original[(context['run'], context['id'])]
    checks = 0
    equal = 0
    differences = []
    for name in sorted({k[0] for k in original}):
        run = a.capture / name
        record = json.loads(gzip.decompress((run / 'record.json.gz').read_bytes()))
        rx = Receiver(profiles, contract, name, 'Carla/Maps/Town10HD_Opt')
        for d in record['decisions']:
            old = (run / 'packets' / (d['id'] + '.json')).read_bytes() if d['geometry'] else None
            motion = body.Motion(half_length=2.3, half_width=1.3, yaw=d['yaw'],
                                 acceleration=0., yaw_rate=0.)
            prior = rx.latest_region()
            if prior and not (prior.established <= d['stamp'] and
                              math.ceil(d['stamp'] * 1e6) < rx._deadlines[prior.identity]):
                prior = None
            assert (prior.identity if prior else None) == d['prior']
            plane = json.loads(old)['raw']['payload']['scope']['plane_z'] if old else 0.
            scope = body.Scope(name, 'Carla/Maps/Town10HD_Opt', tuple(d['query']), plane)
            if (name, d['id']) in original:
                context = original[(name, d['id'])]
                assert context['decision'] == d
                assert body.canonical(context['prior']) == body.canonical(body.asdict(prior) if prior else None)
                with np.load(run / 'clouds' / (d['id'] + '.npz')) as cl:
                    encoded = body.encode_source(cl['xyz'], cl['origin'], d['stamp'], d['stamp'])
                    scope = body.Scope(name, scope.frame_id, scope.query, float(cl['plane_z']))
                source_set = {tuple(x) for x in encoded[1]}
                full = reference_frontier(body.projections(*encoded, profiles, scope, contract),
                                          profiles, scope, motion, prior, encoded[2] / 1e6,
                                          1_000_000)['horizon_us']
                assert full == context['full_input_horizon_us']
                for stage_name, stage in stages.items():
                    for row in stage['rows']:
                        if row['run'] != name or row['id'] != d['id']:
                            continue
                        h_us = round(row['horizon_ms'] * 1000)
                        cost_ms = sum(row[k] for k in ['acquisition_ms', 'generation_ms',
                                                      'verification_ms', 'wire_ms'])
                        assert row['wire_ms'] == 20 + row['packet_bytes'] * 8 / 20_000
                        assert row['acquisition_ms'] == float(d['acquisition_s']) * 1000
                        ticks_us = max(50_000, math.ceil(cost_ms / 50) * 50_000)
                        assert row['usable_us'] == (h_us - math.ceil(cost_ms * 1000)
                                                    if row['geometry'] else None)
                        assert row['tick_action_slack_us'] == (h_us - ticks_us - 200_000
                                                               if row['geometry'] else None)
                        assert row['hypothetical_action_pass'] == bool(row['geometry'] and
                                                                      ticks_us + 200_000 < h_us)
                        if row['repeat'] != 0 or not row['geometry']:
                            continue
                        p = a.results / stage_name / 'packets' / (name + '_' + d['id'] + '_' +
                             row['method'] + '_' + str(round(row['horizon_ms'])) + '.json')
                        blob = p.read_bytes()
                        assert len(blob) == row['packet_bytes']
                        assert body.verify(blob, profiles, scope, contract, motion, prior,
                                           d['stamp'] + .02, 0)
                        payload, o, r = body.decode(body.canonical(json.loads(blob)['raw']),
                                                    profiles, scope, contract)
                        assert payload['reference_us'] == encoded[2]
                        assert payload['horizon_us'] == h_us
                        assert payload['sequence'] == d['sequence']
                        assert np.array_equal(o, encoded[0])
                        assert all(tuple(x) in source_set for x in r)
                        frontier = reference_frontier(body.projections(o, r, encoded[2], profiles,
                                                                       scope, contract), profiles,
                                                      scope, motion, prior, encoded[2] / 1e6,
                                                      1_000_000)['horizon_us']
                        assert row['maximum_subset_horizon_us'] == frontier
                        assert h_us <= frontier <= full
                        checks += 1
                        if stage_name == 'native':
                            reference_method = {'native_greedy': 'greedy', 'native_thin': 'thin',
                                                'greedy': 'greedy', 'repair': 'repair'}[row['method']]
                            q = a.results / 'matched' / 'packets' / (name + '_' + d['id'] + '_' +
                                reference_method + '_' + str(round(row['horizon_ms'])) + '.json')
                            if blob == q.read_bytes():
                                equal += 1
                            else:
                                differences.append(str(p))
            if d['receiver_accepted']:
                assert rx.accept(old, scope, motion, d['receiver_check_time'])
    summaries, menus = [], []
    for stage_name, stage in stages.items():
        groups = {}
        for row in stage['rows']:
            groups.setdefault((row['run'], row['id'], row['method'], row['horizon_ms']), []).append(row)
        for key, rows in groups.items():
            assert len(rows) == 3 and len({r['geometry'] for r in rows}) == 1
            item = dict(stage=stage_name, run=key[0], id=key[1], method=key[2], horizon_ms=key[3],
                        geometry=rows[0]['geometry'],
                        action_pass_repeats=sum(r['hypothetical_action_pass'] for r in rows))
            for k in ['generation_ms', 'verification_ms', 'packet_bytes', 'rays', 'wire_ms',
                      'usable_us', 'tick_action_slack_us']:
                item[k + '_median'] = float(np.median([r[k] for r in rows])) if rows[0][k] is not None else None
            summaries.append(item)
        keys = {(r['run'], r['id'], r['method'], r['repeat']) for r in stage['rows']}
        for key in sorted(keys):
            rows = [r for r in stage['rows'] if (r['run'], r['id'], r['method'], r['repeat']) == key]
            assert len(rows) == 4
            valid = [r for r in rows if r['geometry']]
            spent_ms = sum(r['generation_ms'] + r['verification_ms'] for r in rows)
            paid_candidates = []
            for r in valid:
                cost_ms = r['acquisition_ms'] + spent_ms + r['wire_ms']
                tick_us = max(50_000, math.ceil(cost_ms / 50) * 50_000)
                paid_candidates.append(dict(horizon_ms=r['horizon_ms'],
                                            usable_us=round(r['horizon_ms'] * 1000) - math.ceil(cost_ms * 1000),
                                            tick_action_slack_us=round(r['horizon_ms'] * 1000) - tick_us - 200_000))
            oracle = max(valid, key=lambda r: r['usable_us']) if valid else None
            paid = max(paid_candidates, key=lambda r: r['usable_us']) if paid_candidates else None
            menus.append(dict(stage=stage_name, run=key[0], id=key[1], method=key[2], repeat=key[3],
                              all_generation_and_check_ms=spent_ms,
                              one_candidate_oracle_horizon_ms=oracle['horizon_ms'] if oracle else None,
                              one_candidate_oracle_usable_us=oracle['usable_us'] if oracle else None,
                              paid_all_candidates=paid,
                              paid_menu_action_pass=bool(paid and paid['tick_action_slack_us'] > 0)))
    result = dict(full_packet_checks=checks, native_packet_matches=equal,
                  native_packet_differences=differences, summaries=summaries, menus=menus,
                  scope='Paid menu is an aggregate modeled sequential computation diagnostic, not a deployed controller. No online oracle gain is claimed.',
                  analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['full_packet_checks', 'native_packet_matches',
                                          'native_packet_differences']}))


if __name__ == '__main__':
    main()
