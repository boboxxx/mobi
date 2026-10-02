#!/usr/bin/env python3
"""Verify frozen measured dependencies, then seal this finite artifact."""
import argparse, hashlib, json
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[2];sources={}
    measured=json.loads((a.results/'study/analysis.json').read_bytes())
    fine=json.loads((a.results/'refined/analysis.json').read_bytes())
    for mapping in [measured['source_sha256'],fine['loaded_additional_sources']]:
        for f,h in mapping.items():assert sha(root/f)==h,f;sources[f]=h
    prior=root/'results/streaming_recovery_20261002/source_manifest.json'
    for f,h in json.loads(prior.read_bytes())['source_sha256'].items():
        assert sha(root/f)==h,f;sources[f]=h
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file() and p.suffix in ['.py','.md','.cpp'] and not p.name.startswith('._'):
            sources[str(p.relative_to(root))]=sha(p)
    for p in [root/'experiments/set_observer_20261002/PROTOCOL.md',root/'experiments/set_observer_20261002/REFINEMENT_PROTOCOL.md']:
        expected=measured['protocol_sha256'] if p.name=='PROTOCOL.md' else fine['protocol_sha256']
        assert sha(p)==expected,p
    (a.results/'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,prior_manifest_sha256=sha(prior),
        scope='Actual measured dependencies, frozen prior package dependencies and full finite observer package. Canonical relative paths; no native binaries tracked.'),indent=2,sort_keys=True)+'\n')
    files=sorted(p for p in a.results.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and not p.name.startswith('._'))
    (a.results/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(a.results))+'\n' for p in files))
    print(json.dumps(dict(source_files=len(sources),result_files=len(files),manifest_sha256=sha(a.results/'source_manifest.json'),checksums_sha256=sha(a.results/'SHA256SUMS'))))


if __name__=='__main__':main()
