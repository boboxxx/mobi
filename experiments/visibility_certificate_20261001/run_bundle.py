#!/usr/bin/env python3
"""Finite, receiver-required two-class renewal with serial measured computation."""
import argparse, hashlib, json, socket, time
from pathlib import Path
import numpy as np
from geometry import Profile, plane_witnesses
from proof_packet import canonical
from renewal import renew, verify_all
from run_study import CLASSES, write
import csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / 'packets').mkdir()
    frames = {r['id']: r for r in csv.DictReader((a.capture / 'frames.csv').open())}
    rows = []
    for cloud in sorted((a.capture / 'clouds').glob('*.npz')):
        density, layout, scenario, step = cloud.stem.split('_')
        if scenario == 'free' and step == '00':
            continue  # Cold initialization does not count as a fresh-frame renewal.
        data = np.load(cloud)
        for thin in [1, 8]:
            profiles, templates, scopes = {}, {}, {}
            for name in CLASSES:
                path = a.capture / 'packets' / ('%s_%s_free_00_%d_%s_0.2.json' % (density, layout, thin, name))
                if path.exists():
                    templates[name] = path.read_bytes()
                    profiles[name] = Profile(**json.loads(templates[name])['payload']['profile'])
                    scopes[name] = cloud.stem + ':' + name
            eligible = set(templates) == set(CLASSES)
            blobs = {}
            start = time.perf_counter()
            if eligible:
                w = plane_witnesses(data['xyz'][::thin], data['origin'], data['query'], float(data['probe_z']))
                for name in CLASSES:
                    # Frozen template profile; do not use a per-frame grid selection.
                    blob = renew(templates[name], w, profiles[name], scopes[name], 0.)
                    if blob is not None:
                        blobs[name] = blob
            wire = canonical({k: json.loads(v) for k, v in blobs.items()})
            sender_ms = 1000 * (time.perf_counter() - start)
            start = time.perf_counter()
            blobs = {k: canonical(v) for k, v in json.loads(wire).items()}
            geometry_ok = bool(eligible and verify_all(blobs, profiles, scopes, .02, .05))
            receiver_ms = 1000 * (time.perf_counter() - start)
            age = float(frames[cloud.stem]['acquisition_ms']) / 1000 + (sender_ms + receiver_ms) / 1000 + .02
            timely = bool(geometry_ok and verify_all(blobs, profiles, scopes, age, .05))
            # Include framing bytes of the serialized bundle, not only witness arrays.
            if blobs:
                (a.out / 'packets' / (cloud.stem + '_' + str(thin) + '.json')).write_bytes(wire)
            rows.append(dict(id=cloud.stem, density=density, layout=layout, scenario=scenario,
                             thinning=thin, template_available=eligible, geometry_verified=geometry_ok,
                             timing_budget_passed=timely, sender_ms=sender_ms, receiver_ms=receiver_ms,
                             modeled_total_age_s=age, action_s=.05, target_s=.2,
                             packet_bytes=len(wire) if blobs else 0,
                             missing_classes=','.join(sorted(set(CLASSES)-set(blobs)))))
    write(a.out / 'bundles.csv', rows)
    manifest = dict(host=socket.gethostname(), attempts=len(rows),
                    templates_available=sum(r['template_available'] for r in rows),
                    geometry_passes=sum(r['geometry_verified'] for r in rows),
                    timing_passes=sum(r['timing_budget_passed'] for r in rows),
                    near_accepts=sum(r['geometry_verified'] and r['scenario']=='near' for r in rows),
                    source_sha256={n: hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                                   for n in ['run_bundle.py', 'geometry.py', 'proof_packet.py', 'renewal.py']},
                    scope='Two stipulated classes, current-cloud replay, serial measured CPU, recorded acquisition, modeled 20ms transport and 50ms action. Static scenes, no driving loop.')
    (a.out / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest), flush=True)


if __name__ == '__main__':
    main()
