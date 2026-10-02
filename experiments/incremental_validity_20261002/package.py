#!/usr/bin/env python3
"""Hash actual loaded sources, finite protocols and every preserved result file."""
import argparse, hashlib, json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources = {}
    for stage in ['selected', 'all', 'selected_shared', 'all_shared']:
        study = json.loads((a.results / stage / 'analysis.json').read_bytes())
        for f, h in study['source_sha256'].items():
            assert sha(root / f) == h, f
            if f in sources:
                assert sources[f] == h
            sources[f] = h
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file() and p.suffix in ['.py', '.md'] and not p.name.startswith('._'):
            sources[str(p.relative_to(root))] = sha(p)
    cpp = 'experiments/usable_lease_20261002/cover.cpp'
    sources[cpp] = sha(root / cpp)
    (a.results / 'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,
        scope='Actual loaded runtime modules plus this finite package source/protocol/documentation; AppleDouble is not executable source.'), indent=2, sort_keys=True) + '\n')
    files = sorted(p for p in a.results.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (a.results / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(a.results)) + '\n' for p in files))
    print(json.dumps(dict(source_files=len(sources), result_files=len(files))))


if __name__ == '__main__':
    main()
