#!/usr/bin/env python3
"""Post-run exhaustive closure and same-parent-scope publication checks."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();f=read(E/'freeze.json');d=read(P/'analysis_sheng.json');au=read(P/'audit_sheng.json');pairs=[]
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 for stem,source in [('audit','audit.py'),('summary','summarize.py')]:
  assert (P/(stem+'_local.json')).read_bytes()==(P/(stem+'_sheng.json')).read_bytes();v=read(P/(stem+'_sheng.json'));assert v['source_sha256']==sha(E/source) and v['analysis_sha256']==sha(P/'analysis_sheng.json');pairs.append(dict(stem=stem,sha256=sha(P/(stem+'_sheng.json'))))
 assert au['rows']==len(d['rows'])==2046 and au['actual_packet_checks']==4092 and au['trace_checks']==len(d['traces'])==2880 and au['decision_checks']==92160 and d['policies']==au['policies'] and d['freeze_sha256']==sha(E/'freeze.json')
 assert set(str(p.relative_to(ROOT)) for p in (P/'messages').iterdir())=={m['packet'] for r in d['rows'] for m in r['methods'].values()}
 pre=read(P/'preregistration.json');assert pre['published_source_commit']=='e025f931745589537a1cbcc8e436a09c6e55c297' and pre['freeze_sha256']==sha(E/'freeze.json') and pre['new_timing_outputs_absent'] and pre['parent_data_already_observed'] and pre['model_registry_queries_unchanged'] and not pre['goal_complete']
 repair=read(P/'preflight_repair_receipt.json');assert repair['original_producer_sha256']==sha(E/'produce_at_first_preflight.py') and repair['original_test_sha256']==sha(E/'registration_tests_at_first_preflight.py') and repair['original_freeze_sha256']==sha(E/'freeze_at_first_preflight.json') and repair['corrected_producer_sha256']==sha(E/'produce.py') and repair['corrected_test_sha256']==sha(E/'test_registration.py') and repair['corrected_freeze_sha256']==sha(E/'freeze.json') and repair['first_failure_log_sha256']==sha(P/'tests_local_first_failure.log');assert 'FAILED (errors=2)' in (P/'tests_local_first_failure.log').read_text()
 for host in ('local','sheng'):
  for suffix in ('','_before_timing'):
   s=(P/('tests_'+host+suffix+'.log')).read_text();assert 'Ran 3 tests' in s and s.rstrip().endswith('OK')
 assert (P/'run_terminal.txt').read_text()=='FINITE_MATCHED_REGISTRATION_COMPLETE\n'
 if a.freeze:
  files=sorted(p for p in E.iterdir() if p.is_file())+[ROOT/'research/matched_registration_result_20261004.md',ROOT/'research/query_reuse_problem_20261004.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in files},scope='Frozen matched study/post-processing, report and next-question boundary; rolling project docs not part of this immutable source closure.'))
  write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=3,source_manifest_sha256=sha(P/'publication_source_manifest.json'),parent_models_and_qualification_unchanged=True,full_goal_complete=False,scope='Finite matched shared lightweight registration, not globally minimal context or dynamic-query/state-tightness/physical/MobiCom completion.'))
  files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
 for n,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/n)==h,n
 m=read(P/'artifact_manifest.json');assert set(m['files'])=={str(p.relative_to(ROOT)) for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json'}
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
 print(json.dumps(dict(archived_files=m['file_count'],archived_bytes=m['total_bytes'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
