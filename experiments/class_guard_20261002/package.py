#!/usr/bin/env python3
"""Freeze verified sources/results, retaining the original and corrected models."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results;prior=ROOT/'results/validity_witness_20261002/source_manifest.json';sources=json.loads(prior.read_bytes())['source_sha256'].copy()
    for f,h in sources.items():assert sha(ROOT/f)==h,f
    for stem in ['audit','witness']:assert (r/(stem+'_local.json')).read_bytes()==(r/(stem+'_sheng.json')).read_bytes()
    audit=json.loads((r/'audit_local.json').read_bytes());assert audit['root_fifo_occupancy_charged'] and audit['cost_rows']==5400 and audit['analyzer_sha256']==sha(Path(__file__).with_name('analyze.py')) and audit['audited_data_sha256']==sha(r/'fifo_corrected.json')
    witness=json.loads((r/'witness_local.json').read_bytes());assert witness['cases']==84 and witness['analyzer_sha256']==sha(Path(__file__).with_name('witness_check.py'))
    measured=json.loads((r/'study/analysis.json').read_bytes());corrected=json.loads((r/'fifo_corrected.json').read_bytes());assert corrected['measured_study_sha256']==sha(r/'study/analysis.json') and corrected['fifo_replay_sha256']==sha(Path(__file__).with_name('replay_fifo.py'))
    for f,h in measured['source_sha256'].items():assert sha(ROOT/f)==h,f
    for f,h in measured['input_sha256'].items():assert sha(ROOT/f)==h,f
    for library in json.loads((r/'build_dependencies.json').read_bytes())['libraries']:assert sha(ROOT/library['source'])==library['source_sha256']
    for f in ['tests_local.txt','tests_sheng.txt','fifo_tests_local.txt','fifo_tests_sheng.txt']:
        value=(r/f).read_text();assert '\nOK\n' in value and ('Ran 8 tests' in value if f.startswith('tests') else 'Ran 3 tests' in value)
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file() and p.suffix in ['.py','.cpp','.md']:sources[str(p.relative_to(ROOT))]=sha(p)
    report=ROOT/'research/class_guard_result_20261002.md';sources[str(report.relative_to(ROOT))]=sha(report)
    (r/'source_manifest.json').write_text(json.dumps(dict(source_sha256=sources,prior_manifest_sha256=sha(prior),scope='Frozen inherited112 sources and new class-guard/corrected-FIFO/witness package. Main README/completion ledger remain mutable. Initial-model source/audit is retained as a result artifact.'),indent=2,sort_keys=True)+'\n')
    files=sorted(p for p in r.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and not p.name.startswith('._') and '__pycache__' not in p.parts)
    (r/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(r))+'\n' for p in files));print(json.dumps(dict(source_files=len(sources),result_files=len(files),manifest_sha256=sha(r/'source_manifest.json'),checksums_sha256=sha(r/'SHA256SUMS'),report_sha256=sha(report))))
if __name__=='__main__':main()
