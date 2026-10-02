#!/usr/bin/env python3
"""Freeze source graph and all results after independent cross-host audits."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results;prior=ROOT/'results/recursive_validity_20261002/source_manifest.json';sources=json.loads(prior.read_bytes())['source_sha256'].copy()
    for f,h in sources.items():assert sha(ROOT/f)==h,f
    for prefix in ['audit','extension_audit','extra_ray_audit']:assert (r/(prefix+'_sheng.json')).read_bytes()==(r/(prefix+'_local.json')).read_bytes()
    for study in ['study','ellipsoid_study','heading_study','extra_ray_study']:
        s=json.loads((r/study/'analysis.json').read_bytes())
        for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h,f
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file() and p.suffix in ['.py','.cpp','.md']:sources[str(p.relative_to(ROOT))]=sha(p)
    report=ROOT/'research/validity_witness_result_20261002.md';sources[str(report.relative_to(ROOT))]=sha(report)
    (r/'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,prior_manifest_sha256=sha(prior),scope='Frozen inherited87 source dependencies and this finite witness/shape/heading/extra-ray package; root README/completion ledger remain mutable.'),indent=2,sort_keys=True)+'\n')
    files=sorted(p for p in r.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and not p.name.startswith('._'))
    (r/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(r))+'\n' for p in files));print(json.dumps(dict(source_files=len(sources),result_files=len(files),manifest_sha256=sha(r/'source_manifest.json'),checksums_sha256=sha(r/'SHA256SUMS'),report_sha256=sha(report))))
if __name__=='__main__':main()
