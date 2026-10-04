#!/usr/bin/env python3
"""Closure of archived development evidence and publication sources."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();d=read(P/'analysis_sheng.json');au=read(P/'audit_sheng.json');su=read(P/'summary_sheng.json');pairs=[]
 for stem,source in [('audit','audit.py'),('summary','summarize.py'),('gap_witness','diagnose_gap.py')]:
  assert (P/(stem+'_local.json')).read_bytes()==(P/(stem+'_sheng.json')).read_bytes(),stem
  v=read(P/(stem+'_sheng.json'));assert v['source_sha256']==sha(E/source) and v['analysis_sha256']==sha(P/'analysis_sheng.json');pairs.append(dict(stem=stem,sha256=sha(P/(stem+'_sheng.json'))))
 freeze=read(E/'freeze.json');assert d['source_hashes']==freeze['sources']
 for mapping in (d['source_hashes'],d['input_hashes'],freeze['input_hashes']):
  for n,h in mapping.items():assert sha(ROOT/n)==h,n
 assert d['context']['source_hashes']==freeze['sources'] and au['analysis_sha256']==sha(P/'analysis_sheng.json') and su['audit_sha256']==sha(P/'audit_sheng.json');assert d['test_frames']==len(d['rows'])==2076 and d['planned_test_episodes']==360;assert au['trace_checks']==5760 and au['decision_checks']==184320
 ref=read(ROOT/'results/background_frontend_20261004/body_support_sheng.json');old=read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json');ctx=d['context'];assert ctx['slacks_um']=={k:v['development_slack_um'] for k,v in ref['registry'].items()};assert ctx['background_sha256']==sha(ROOT/'results/background_frontend_20261004/background.json');assert ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000) and ctx['cap_us']==500000 and ctx['query_radius_um']==750000 and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['point_quantization_allowance_um']==8000;assert ctx['raw_transport']['contract']==old['contract_sha256'] and ctx['raw_transport']['calibration']==old['calibration_sha256']
 for r in old['rows']:assert ctx['raw_transport']['transforms'][str(r['layout'])]==r['sensor_transform']['matrix']
 for host in ('local','sheng'):
  log=(P/('tests_'+host+'.log')).read_text();assert 'Ran 13 tests' in log and log.rstrip().endswith('OK')
 assert (P/'run_terminal.txt').read_text()=='FINITE_BODY_EXPIRY_COMPLETE\n';assert su['statuses']==dict(bounded=2072,refused=4) and su['excluded_episodes']==0 and su['bracket_distance_um']['maximum']<=2 and su['bracket_age_us']['maximum']<=1
 witness=read(P/'gap_witness_sheng.json');assert len(witness['witnesses'])==53 and witness['counts_by_class']['vehicle.mercedes.sprinter']==32
 first=read(E/'freeze_at_first_run.json');assert sha(E/'evaluate_at_first_run.py')==first['sources'][str((E/'evaluate.py').relative_to(ROOT))];assert (E/'evaluate_at_first_run.py').read_text().replace('p=a.results;p.mkdir','p=a.results.resolve();p.mkdir')==(E/'evaluate.py').read_text();assert 'ValueError' in (P/'at_first_run/evaluate_sheng.log').read_text()
 if a.freeze:
  sources=sorted(p for p in E.iterdir() if p.is_file() and p.name!='proposer.so')+[ROOT/'research/body_expiry_result_20261004.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sources}))
  write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=13,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Finite reused-data body-set expiry, measured four-wire comparison and abstract contact diagnosis. No prospective risk qualification, unknown inventory, physical/live closed loop or MobiCom contribution established.'))
  files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
 for n,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/n)==h,n
 m=read(P/'artifact_manifest.json');assert {str(p.relative_to(ROOT)) for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json'}==set(m['files'])
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
 print(json.dumps(dict(result_files=m['file_count'],total_bytes=m['total_bytes'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
