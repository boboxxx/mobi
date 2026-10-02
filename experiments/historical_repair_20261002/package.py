"""Assemble and verify immutable provenance for the completed finite package."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/historical_repair_20261002'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'results/class_guard_20261002/source_manifest.json';sources=json.loads(prior.read_bytes())['source_sha256']
for p,h in sources.items():assert sha(ROOT/p)==h,p
for p in Path(__file__).resolve().parent.iterdir():
 if p.is_file() and p.suffix in ('.py','.md'):sources[str(p.relative_to(ROOT))]=sha(p)
sources['research/historical_repair_result_20261002.md']=sha(ROOT/'research/historical_repair_result_20261002.md')
(OUT/'source_manifest.json').write_text(json.dumps(dict(prior_manifest_sha256=sha(prior),source_sha256=sources,scope='All inherited frozen sources plus this finite historical-repair package; native libraries inherited unchanged'),indent=2)+'\n')
s=json.loads((OUT/'study/analysis.json').read_bytes());assert len(s['runs'])==270 and sum(len(x['rows']) for x in s['runs'])==5400
for f,h in s['source_sha256'].items():assert sha(Path(__file__).parent/f)==h
for name in ['audit','witness']:
 assert (OUT/(name+'_local.json')).read_bytes()==(OUT/(name+'_sheng.json')).read_bytes()
 a=json.loads((OUT/(name+'_local.json')).read_bytes());assert a['analyzer_sha256']==sha(Path(__file__).with_name('analyze.py' if name=='audit' else 'witness_check.py'))
for key in ['audit_local.json','witness_local.json']:
 a=json.loads((OUT/key).read_bytes())
 for p,h in a['input_sha256'].items():assert sha(ROOT/p)==h,p
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(OUT))+'\n' for p in files))
print(json.dumps(dict(result_entries=len(files),source_entries=len(sources),source_manifest_sha256=sha(OUT/'source_manifest.json'),checksums_sha256=sha(OUT/'SHA256SUMS'),study_sha256=sha(OUT/'study/analysis.json'),report_sha256=sha(ROOT/'research/historical_repair_result_20261002.md'))))
