#!/usr/bin/env python3
import argparse, hashlib, json, shutil, tarfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--tar', type=Path, required=True)
    a = ap.parse_args()
    stages = [json.loads((a.results / k / 'analysis.json').read_bytes()) for k in ['matched', 'native']]
    audit = json.loads((a.results / 'audit.json').read_bytes())
    assert audit['full_packet_checks'] == 112
    assert audit['native_packet_matches'] == 64 and not audit['native_packet_differences']
    assert all(len(s['rows']) == 288 for s in stages)
    build = json.loads((a.results / 'build.json').read_bytes())
    assert build['cpp_sha256'] == hashlib.sha256(Path('experiments/usable_lease_20261002/cover.cpp').read_bytes()).hexdigest()
    assert stages[1]['native_library_sha256'] == build['binary_sha256']
    source = {}
    for s in stages:
        source.update(s['source_sha256'])
    for p in Path('experiments/usable_lease_20261002').iterdir():
        if p.is_file() and p.suffix in ['.py', '.cpp', '.md']:
            source[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    for f, h in source.items():
        assert hashlib.sha256(Path(f).read_bytes()).hexdigest() == h, f
    metadata = {f: h for f, h in source.items() if Path(f).name.startswith('._')}
    for f in metadata:
        p = a.results / 'archived_metadata' / f
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, p)
    source = {f: h for f, h in source.items() if f not in metadata}
    previous = a.results / 'source_manifest.json'
    initial = a.results / 'source_manifest_initial.json'
    if previous.exists() and not initial.exists():
        shutil.copyfile(previous, initial)
    snapshot = dict(source_sha256=source, archival_metadata_sha256=metadata,
                    metadata_scope='AppleDouble files incidentally matched the old dependency glob; they are not executable Python source. Original benchmark manifests are preserved and all metadata bytes archived separately.',
                    protocol_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in Path('experiments/usable_lease_20261002').glob('*PROTOCOL.md')},
                    full_packet_checks=112, native_packet_matches=64,
                    benchmark_calls=576, distinct_unit_tests=8,
                    geometry_calls=sum(sum(r['geometry'] for r in s['rows']) for s in stages),
                    hypothetical_action_passes=sum(sum(r['hypothetical_action_pass'] for r in s['rows']) for s in stages),
                    paid_menu_action_passes=sum(m['paid_menu_action_pass'] for m in audit['menus']),
                    no_new_carla_process=True)
    (a.results / 'source_manifest.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    files = sorted(p for p in a.results.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (a.results / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
                                          str(p.relative_to(a.results)) + '\n' for p in files))
    with tarfile.open(a.tar, 'w:gz') as tf:
        tf.add(a.results, arcname=str(a.results))
    print(json.dumps({k: v for k, v in snapshot.items() if k not in ['source_sha256', 'protocol_sha256']}))


if __name__ == '__main__':
    main()
