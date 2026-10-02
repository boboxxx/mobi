import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/physical_contract_20261002'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'results/historical_repair_20261002/source_manifest.json';sources=json.loads(prior.read_bytes())['source_sha256']
for p,h in sources.items():assert sha(ROOT/p)==h,p
for p in Path(__file__).resolve().parent.iterdir():
 if p.is_file() and p.suffix in ['.py','.md','.ps1']:sources[str(p.relative_to(ROOT))]=sha(p)
sources['research/physical_contract_result_20261002.md']=sha(ROOT/'research/physical_contract_result_20261002.md')
(OUT/'source_manifest.json').write_text(json.dumps(dict(prior_manifest_sha256=sha(prior),source_sha256=sources,scope='Inherited frozen sources plus fresh physical-contract falsification package; previous results unchanged'),indent=2)+'\n')
for k in ['analysis','audit']:assert (OUT/(k+'_local.json')).read_bytes()==(OUT/(k+'_sheng.json')).read_bytes()
a=json.loads((OUT/'analysis_sheng.json').read_bytes());u=json.loads((OUT/'audit_sheng.json').read_bytes());assert u['analysis_sha256']==sha(OUT/'analysis_sheng.json');assert u['auditor_sha256']==sha(Path(__file__).with_name('audit.py'));assert a['source_sha256']==sha(Path(__file__).with_name('analyze.py'))
for p,h in a['input_sha256'].items():assert sha(ROOT/p)==h
summary=dict(frames=u['frames'],raw_rays=u['raw_rays'],corner_checks=u['corner_checks'],robust_exclusions=u['robust_exclusions'],actual_outer_failures=u['actual_outer_failures'],any_center_outer_failures=u['any_center_outer_failures'],groups=a['groups'],analysis_sha256=sha(OUT/'analysis_sheng.json'),audit_sha256=sha(OUT/'audit_sheng.json'),scope='Fresh finite necessary-condition falsification; no physical calibration or new driving authority')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');files=sorted(x for x in OUT.rglob('*') if x.is_file() and x.name!='SHA256SUMS');(OUT/'SHA256SUMS').write_text(''.join(sha(x)+'  '+str(x.relative_to(OUT))+'\n' for x in files));print(json.dumps(dict(sources=len(sources),result_entries=len(files),bytes=sum(x.stat().st_size for x in files),source_manifest_sha256=sha(OUT/'source_manifest.json'),checksums_sha256=sha(OUT/'SHA256SUMS'),report_sha256=sha(ROOT/'research/physical_contract_result_20261002.md'))))
