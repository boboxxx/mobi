#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[2];sources={}
    study=json.loads((a.results/'study/analysis.json').read_bytes())
    for f,h in study['source_sha256'].items():assert sha(root/f)==h,f;sources[f]=h
    for name in ['continuity_recovery_20261002','streaming_recovery_20261002']:
        for p in (root/'experiments'/name).iterdir():
            if p.is_file() and p.suffix in ['.py','.md','.cpp'] and not p.name.startswith('._'):sources[str(p.relative_to(root))]=sha(p)
    f='experiments/usable_lease_20261002/cover.cpp';sources[f]=sha(root/f)
    (a.results/'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,scope='Actual measured loaded sources plus both finite packages and kernel dependency; sorted canonical source paths.'),indent=2,sort_keys=True)+'\n')
    files=sorted(p for p in a.results.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and not p.name.startswith('._'))
    (a.results/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(a.results))+'\n' for p in files))
    print(json.dumps(dict(source_files=len(sources),result_files=len(files))))


if __name__=='__main__':main()
