#!/usr/bin/env python3
import argparse, copy, gzip, hashlib, json, math, os, socket, sys, time
from pathlib import Path
import numpy as np
from patch import body, repair as patch
from efficient_renew import repair as old_repair
from native_pack import library, pack as fallback
from profile_source import SELECT
from fast_path import Receiver
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'expiry_frontier_20261001'))
from frontier import frontier as full_frontier

METHODS = ['old', 'nearest', 'gap_greedy']


def provenance(encoded, origins, rays):
    source_o, source_r, _ = encoded
    def key(o, r):
        return tuple(o[r[0]]) + tuple(r[1:])
    original = {key(source_o, r) for r in source_r}
    return all(key(origins, r) in original for r in rays)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['selected', 'all'], required=True)
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(exist_ok=False)
    (a.out / 'packets').mkdir()
    assert all(os.environ.get(n) == '1' for n in
               ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'])
    start = time.perf_counter();library();load_ms = (time.perf_counter() - start) * 1000
    profiles = dict(small=body.Profile(r_min=.2, r_max=.4, query_radius=0., step=.05, error=0.),
                    vehicle=body.Profile(r_min=.55, r_max=2.5, query_radius=0., step=.1, error=0.))
    contract = body.Contract()
    names = (sorted(SELECT) if a.mode == 'selected' else
             sorted(p.name for p in a.capture.iterdir() if (p / 'record.json.gz').exists()))
    rng = np.random.default_rng(20261003)
    rows, contexts, hashes = [], [], {}
    states = 0

    def read(p):
        value = p.read_bytes();hashes[str(p)] = hashlib.sha256(value).hexdigest()
        return value

    for name in names:
        run = a.capture / name
        record = json.loads(gzip.decompress(read(run / 'record.json.gz')))
        rx = Receiver(profiles, contract, name, 'Carla/Maps/Town10HD_Opt')
        template = None
        for d in record['decisions']:
            old = read(run / 'packets' / (d['id'] + '.json')) if d['geometry'] else None
            plane = json.loads(old)['raw']['payload']['scope']['plane_z'] if old else 0.
            scope = body.Scope(name, 'Carla/Maps/Town10HD_Opt', tuple(d['query']), plane)
            motion = body.Motion(half_length=2.3, half_width=1.3, yaw=d['yaw'],
                                 acceleration=0., yaw_rate=0.)
            prior = rx.latest_region()
            if prior and not (prior.established <= d['stamp'] and
                              math.ceil(d['stamp'] * 1e6) < rx._deadlines[prior.identity]):
                prior = None
            assert (prior.identity if prior else None) == d['prior']
            if a.mode == 'all' or d['id'] in SELECT[name]:
                p = run / 'clouds' / (d['id'] + '.npz');read(p)
                with np.load(p) as cl:
                    points, origin = cl['xyz'].copy(), cl['origin'].copy()
                    scope = body.Scope(name, scope.frame_id, scope.query, float(cl['plane_z']))
                encoded = body.encode_source(points, origin, d['stamp'], d['stamp'])
                full_h = None
                if a.mode == 'selected':
                    full_h = full_frontier(body.projections(*encoded, profiles, scope, contract),
                                           profiles, scope, motion, prior, encoded[2] / 1e6,
                                           1_000_000)['horizon_us']
                contexts.append(dict(run=name, id=d['id'], decision=d,
                                     prior=body.asdict(prior) if prior else None,
                                     full_input_horizon_us=full_h,
                                     template_sha256=hashlib.sha256(template).hexdigest() if template else None))
                horizons = [.4, .45, .475] if a.mode == 'selected' else [.475]
                repetitions = 3 if a.mode == 'selected' else 1
                for h in horizons:
                    args = (points, origin, d['stamp'], d['stamp'], profiles, scope,
                            contract, motion, prior, h, d['sequence'])
                    for repeat in range(repetitions):
                        order = (rng.permutation(METHODS).tolist() if a.mode == 'selected'
                                 else METHODS[states % 3:] + METHODS[:states % 3])
                        for method in order:
                            diag = {}
                            begin = time.perf_counter()
                            if method == 'old':
                                blob = old_repair(template, *args) if template else None
                                diag['branch'] = 'old_repair' if blob else 'rejected'
                            else:
                                blob = patch(template, *args, strategy='greedy' if method == 'gap_greedy' else 'nearest', diagnostics=diag)
                            used_fallback = blob is None
                            if used_fallback:
                                blob = fallback(*args, strategy='greedy')
                            gen_ms = (time.perf_counter() - begin) * 1000
                            cv_ms, max_h, rays, temporal_accept = 0., None, 0, False
                            rx_probe = copy.deepcopy(rx) if blob else None
                            if blob:
                                begin = time.perf_counter()
                                assert rx_probe.accept(blob, scope, motion, d['stamp'] + .02)
                                cv_ms = (time.perf_counter() - begin) * 1000
                                payload, o, r = body.decode(body.canonical(json.loads(blob)['raw']),
                                                            profiles, scope, contract)
                                assert payload['reference_us'] == encoded[2]
                                assert payload['horizon_us'] == math.floor(h * 1e6)
                                assert provenance(encoded, o, r)
                                rays = len(r)
                                if repeat == 0:
                                    if a.mode == 'selected':
                                        max_h = full_frontier(body.projections(o, r, encoded[2], profiles,
                                                                               scope, contract), profiles,
                                                              scope, motion, prior, encoded[2] / 1e6,
                                                              1_000_000)['horizon_us']
                                        assert payload['horizon_us'] <= max_h <= full_h
                                    (a.out / 'packets' / (name + '_' + d['id'] + '_' + method +
                                     '_' + str(round(h * 1000)) + '.json')).write_bytes(blob)
                            acq_ms = float(d['acquisition_s']) * 1000
                            wire_ms = 20 + (len(blob) * 8 / 20_000 if blob else 0)
                            cost_ms = acq_ms + gen_ms + cv_ms + wire_ms
                            ticks_us = max(50_000, math.ceil(cost_ms / 50) * 50_000)
                            h_us = math.floor(h * 1e6)
                            if blob:
                                temporal_accept = copy.deepcopy(rx).accept(blob, scope, motion,
                                                                           (encoded[2] + ticks_us) / 1e6)
                            # Preserve the original fixed-link condition as a separate diagnostic.
                            original_wire_ms = (20 if record.get('link_mbps') == 0 else wire_ms)
                            original_ticks_us = max(50_000, math.ceil((acq_ms + gen_ms + cv_ms +
                                                                     original_wire_ms) / 50) * 50_000)
                            row = dict(run=name, id=d['id'], phase=d['phase'], repeat=repeat, order=order,
                                       method=method, horizon_ms=h * 1000, geometry=blob is not None,
                                       used_fallback=used_fallback, repair_diagnostics=diag,
                                       generation_ms=gen_ms, verification_ms=cv_ms, acquisition_ms=acq_ms,
                                       wire_ms=wire_ms, original_wire_ms=original_wire_ms,
                                       packet_bytes=len(blob) if blob else 0, rays=rays,
                                       subset_frontier_us=max_h,
                                       usable_us=h_us - math.ceil(cost_ms * 1000) if blob else None,
                                       tick_age_us=ticks_us, hypothetical_temporal_accept=temporal_accept,
                                       action_slack_us=h_us - ticks_us - 200_000 if blob else None,
                                       hypothetical_action_pass=bool(blob and temporal_accept and ticks_us + 200_000 < h_us),
                                       original_link_action_pass=bool(blob and original_ticks_us + 200_000 < h_us))
                            rows.append(row);print(json.dumps(row), flush=True)
                states += 1
            if old:
                template = old
            if d['receiver_accepted']:
                assert rx.accept(old, scope, motion, d['receiver_check_time'])
    assert (states, len(rows)) == ((6, 162) if a.mode == 'selected' else (384, 1152))
    root = Path(__file__).resolve().parents[2]
    source = {}
    for module in list(sys.modules.values()):
        f = getattr(module, '__file__', None)
        if f:
            p = Path(f).resolve()
            if p.is_file() and root in p.parents and p.suffix == '.py':
                source[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(host=socket.gethostname(), mode=a.mode, states=states, rows=rows, contexts=contexts,
                  input_sha256=hashes, source_sha256=source, library_load_ms=load_ms,
                  library_sha256=hashlib.sha256(Path(os.environ['MOBI_COVER_LIBRARY']).read_bytes()).hexdigest(),
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  scope='Retrospective original-receiver-history paired replay; costs observed, not WCET; no new driving or real wireless claim.')
    (a.out / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
