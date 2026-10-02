#!/usr/bin/env python3
"""Finite matched archived-input study. No candidate diagnostic is free online."""
import argparse, gzip, hashlib, json, math, os, socket, sys, time
from pathlib import Path
import numpy as np
from thin import body, pack as thin_pack
from efficient_renew import repair
from profile_source import SELECT
from fast_path import Receiver
from compress import pack as greedy_pack
from shell_frontier import frontier as quick_frontier
from frontier import frontier as full_frontier

HORIZONS = [.2, .4, .45, .475]
METHODS = ['nearest', 'greedy', 'repair', 'thin']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(exist_ok=False)
    (a.out / 'packets').mkdir()
    assert all(os.environ.get(n) == '1' for n in
               ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'])
    profiles = dict(small=body.Profile(r_min=.2, r_max=.4, query_radius=0., step=.05, error=0.),
                    vehicle=body.Profile(r_min=.55, r_max=2.5, query_radius=0., step=.1, error=0.))
    contract = body.Contract()
    rng = np.random.default_rng(20261002)
    rows, contexts, inputs = [], [], {}
    states = 0

    def read(p):
        value = p.read_bytes()
        inputs[str(p)] = hashlib.sha256(value).hexdigest()
        return value

    for name, selected in SELECT.items():
        run = a.capture / name
        record = json.loads(gzip.decompress(read(run / 'record.json.gz')))
        rx = Receiver(profiles, contract, name, 'Carla/Maps/Town10HD_Opt')
        template = None
        for d in record['decisions']:
            scope = body.Scope(name, 'Carla/Maps/Town10HD_Opt', tuple(d['query']),
                               0.)  # Updated from the actual cloud below.
            motion = body.Motion(half_length=2.3, half_width=1.3, yaw=d['yaw'],
                                 acceleration=0., yaw_rate=0.)
            prior = rx.latest_region()
            if prior and not (prior.established <= d['stamp'] and
                              math.ceil(d['stamp'] * 1e6) < rx._deadlines[prior.identity]):
                prior = None
            assert (prior.identity if prior else None) == d['prior']
            old = read(run / 'packets' / (d['id'] + '.json')) if d['geometry'] else None
            # Original packets give the plane for replay; source-selected inputs
            # additionally check it against the raw cloud.
            if old:
                scope = body.Scope(name, scope.frame_id, scope.query,
                                   json.loads(old)['raw']['payload']['scope']['plane_z'])
            if d['id'] in selected:
                cloud_path = run / 'clouds' / (d['id'] + '.npz')
                read(cloud_path)
                with np.load(cloud_path) as cl:
                    points, origin, plane = cl['xyz'].copy(), cl['origin'].copy(), float(cl['plane_z'])
                scope = body.Scope(name, scope.frame_id, scope.query, plane)
                encoded = body.encode_source(points, origin, d['stamp'], d['stamp'])
                full_results = body.projections(*encoded, profiles, scope, contract)
                full_h = quick_frontier(full_results, profiles, scope, motion, prior,
                                         encoded[2] / 1e6, 1_000_000)
                full_check = full_frontier(full_results, profiles, scope, motion, prior,
                                           encoded[2] / 1e6, 1_000_000)
                assert full_h['horizon_us'] == full_check['horizon_us']
                source_set = {tuple(x) for x in encoded[1]}
                contexts.append(dict(run=name, id=d['id'], decision=d,
                                     prior=body.asdict(prior) if prior else None,
                                     full_input_horizon_us=full_h['horizon_us']))
                states += 1
                for horizon in HORIZONS:
                    args = (points, origin, d['stamp'], d['stamp'], profiles, scope,
                            contract, motion, prior, horizon, d['sequence'])
                    methods = dict(nearest=lambda: body.pack(*args),
                                   greedy=lambda: greedy_pack(*args),
                                   thin=lambda: thin_pack(*args))

                    def renewal():
                        b = repair(template, *args) if template else None
                        return b if b else greedy_pack(*args)

                    methods['repair'] = renewal
                    for repeat in range(3):
                        order = rng.permutation(METHODS).tolist()
                        for position, method in enumerate(order):
                            begin = time.perf_counter()
                            blob = methods[method]()
                            generation_ms = (time.perf_counter() - begin) * 1000
                            verify_ms = 0.
                            max_h = None
                            rays = 0
                            if blob:
                                begin = time.perf_counter()
                                assert body.verify(blob, profiles, scope, contract, motion,
                                                   prior, d['stamp'] + .02, 0)
                                verify_ms = (time.perf_counter() - begin) * 1000
                                payload, origins, selected_rays = body.decode(
                                    body.canonical(json.loads(blob)['raw']), profiles, scope, contract)
                                assert payload['horizon_us'] == math.floor(horizon * 1e6)
                                assert np.array_equal(origins, encoded[0])
                                assert all(tuple(x) in source_set for x in selected_rays)
                                rays = len(selected_rays)
                                if repeat == 0:
                                    results = body.projections(origins, selected_rays,
                                                               payload['reference_us'], profiles,
                                                               scope, contract)
                                    f = quick_frontier(results, profiles, scope, motion, prior,
                                                       payload['reference_us'] / 1e6, 1_000_000)
                                    ref = full_frontier(results, profiles, scope, motion, prior,
                                                        payload['reference_us'] / 1e6, 1_000_000)
                                    assert f['horizon_us'] == ref['horizon_us']
                                    max_h = f['horizon_us']
                                    assert payload['horizon_us'] <= max_h <= full_h['horizon_us']
                                    (a.out / 'packets' / (name + '_' + d['id'] + '_' + method +
                                     '_' + str(round(horizon * 1000)) + '.json')).write_bytes(blob)
                            acquisition_ms = float(d['acquisition_s']) * 1000
                            wire_ms = 20 + (len(blob) * 8 / 20_000 if blob else 0)
                            cost_ms = acquisition_ms + generation_ms + verify_ms + wire_ms
                            available_us = math.ceil(cost_ms * 1000)
                            tick_age_us = max(50_000, math.ceil(cost_ms / 50) * 50_000)
                            h_us = math.floor(horizon * 1e6)
                            row = dict(run=name, id=d['id'], repeat=repeat, order=order,
                                       order_position=position, method=method, horizon_ms=horizon * 1000,
                                       generation_ms=generation_ms, verification_ms=verify_ms,
                                       acquisition_ms=acquisition_ms, wire_ms=wire_ms,
                                       packet_bytes=len(blob) if blob else 0, rays=rays,
                                       geometry=blob is not None, maximum_subset_horizon_us=max_h,
                                       usable_us=h_us - available_us if blob else None,
                                       tick_action_slack_us=h_us - tick_age_us - 200_000 if blob else None,
                                       hypothetical_action_pass=bool(blob and tick_age_us + 200_000 < h_us))
                            rows.append(row)
                            print(json.dumps(row), flush=True)
            if old:
                template = old
            if d['receiver_accepted']:
                assert rx.accept(old, scope, motion, d['receiver_check_time'])
    assert states == 6 and len(rows) == 6 * 4 * 3 * 4
    source = {}
    for directory in ['usable_lease_20261002', 'online_evidence_20261002',
                      'body_evidence_20261001', 'evidence_loop_20261001',
                      'expiry_frontier_20261001', 'ray_proof_v2_20261001',
                      'visibility_uncertainty_20261001', 'visibility_certificate_20261001',
                      'policy_runtime_20261001', 'policy_evidence_20261001']:
        for p in (Path(__file__).resolve().parents[1] / directory).glob('*.py'):
            source[str(p.relative_to(Path(__file__).resolve().parents[2]))] = hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(host=socket.gethostname(), rows=rows, contexts=contexts,
                  input_sha256=inputs, source_sha256=source,
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  thread_environment={n: os.environ.get(n) for n in
                                      ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']},
                  scope='Archived-input matched timing diagnostic; no new closed loop, WCET, or novelty claim.')
    (a.out / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
