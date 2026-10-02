#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();root=Path(__file__).resolve().parents[2];sources={}
    studies=[json.loads((a.results/study/'analysis.json').read_bytes()) for study in ['study','dictionary_study']];prior=root/'results/compact_observer_20261002/source_manifest.json'
    assert all(sha(prior)==s['baseline_manifest_sha256'] for s in studies)
    for mapping in [s['source_sha256'] for s in studies]+[json.loads(prior.read_bytes())['source_sha256']]:
        for f,h in mapping.items():assert sha(root/f)==h,f;sources[f]=h
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file() and p.suffix in ['.py','.md'] and not p.name.startswith('._'):sources[str(p.relative_to(root))]=sha(p)
    for s,name in zip(studies,['PROTOCOL.md','DICTIONARY_PROTOCOL.md']):assert sha(Path(__file__).with_name(name))==s['protocol_sha256']
    (a.results/'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,prior_manifest_sha256=sha(prior),scope='Frozen measured dependencies, complete prior manifest and finite recursive study source.'),indent=2,sort_keys=True)+'\n')
    files=sorted(p for p in a.results.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and not p.name.startswith('._'))
    (a.results/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(a.results))+'\n' for p in files))
    print(json.dumps(dict(source_files=len(sources),result_files=len(files),manifest_sha256=sha(a.results/'source_manifest.json'),checksums_sha256=sha(a.results/'SHA256SUMS'))))
if __name__=='__main__':main()
