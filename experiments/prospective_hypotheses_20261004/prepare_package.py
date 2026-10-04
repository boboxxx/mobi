#!/usr/bin/env python3
"""Pin complete finite-batch sources, frozen inputs and all publishable artifacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = Path(__file__).resolve().parent
P = ROOT / 'results' / E.name


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def main():
    sources, inputs = {}, {}
    for name in ('freeze.json', 'measurement_freeze.json',
                 'minimal_registration_freeze.json'):
        frozen = json.loads((E / name).read_bytes())
        for section, target in (('sources', sources), ('inputs', inputs)):
            for n, h in frozen[section].items():
                assert sha(ROOT / n) == h, n
                assert n not in target or target[n] == h, n
                target[n] = h
    for f in sorted(E.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts:
            assert not f.is_symlink()
            sources[str(f.relative_to(ROOT))] = sha(f)
    for n in ('research/expiry_incomplete_observation_reasoning_20261004.md',
              'research/prospective_hypotheses_result_20261004.md'):
        sources[n] = sha(ROOT / n)
    save(P / 'publication_source_manifest.json', dict(
        sources=sources, inputs=inputs,
        scope='Complete finite-batch code and frozen dependencies, plus post-test '
              'descriptive reporting tools. No rolling root documentation.'))
    archive = json.loads((P / 'archive.json').read_bytes())
    excluded = {'artifact_manifest.json', 'verification_local.json',
                'verification_sheng.json', *archive['logical_files']}
    files = {}
    for f in sorted(P.rglob('*')):
        if f.is_file() and f.name not in excluded:
            assert not f.is_symlink()
            files[str(f.relative_to(ROOT))] = dict(bytes=f.stat().st_size,
                                                   sha256=sha(f))
    save(P / 'artifact_manifest.json', dict(
        files=files, file_count=len(files),
        total_bytes=sum(x['bytes'] for x in files.values()),
        exclusions=sorted(excluded),
        scope='Complete published artifact tree. Three logical JSON files are '
              'losslessly stored in the hashed gzip archives; restore for replay. '
              'The manifest and its two verification receipts are non-circular exclusions.'))
    print('FINITE_PUBLICATION_MANIFESTS_PREPARED', len(sources), len(inputs),
          len(files), flush=True)


if __name__ == '__main__':
    main()
