#!/usr/bin/env python3
"""Closure of finite development results, deterministic pairs and publications."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();d=read(P/'analysis_sheng.json');au=read(P/'audit_sheng.json');s=read(P/'summary_sheng.json');x=read(P/'raw_optimized_sheng.json');diag=read(P/'diagnostic_sheng.json');tilt=read(P/'tilt_prior_lower_bound_sheng.json');pairs=[]
 for stem,source,key,target in [('audit','audit.py','analysis_sha256','analysis_sheng.json'),('summary','summarize.py','analysis_sha256','analysis_sheng.json'),('raw_optimized_audit','audit_raw_optimized.py','analysis_sha256','raw_optimized_sheng.json'),('diagnostic','diagnose.py',None,None),('tilt_prior_lower_bound','tilt_prior_lower_bound.py',None,None)]:
  assert (P/(stem+'_local.json')).read_bytes()==(P/(stem+'_sheng.json')).read_bytes(),stem
  v=read(P/(stem+'_sheng.json'));assert v['source_sha256']==sha(E/source)
  if key:assert v[key]==sha(P/target)
  if 'input_hashes' in v:
   for n,h in v['input_hashes'].items():assert sha(ROOT/n if '/' in n else P/n)==h,n
  pairs.append(dict(stem=stem,sha256=sha(P/(stem+'_sheng.json'))))
 f=read(E/'freeze.json');assert d['source_hashes']==d['context']['source_hashes']==f['sources']
 for mapping in (d['source_hashes'],d['input_hashes'],f['input_hashes']):
  for n,h in mapping.items():assert sha(ROOT/n)==h,n
 rf=read(E/'raw_optimization_freeze.json');assert x['freeze_sha256']==sha(E/'raw_optimization_freeze.json')
 for section in ('sources','inputs'):
  for n,h in rf[section].items():assert sha(ROOT/n)==h,n
 assert len(d['rows'])==au['frames']==5304 and sum(r['split']=='test' for r in d['rows'])==len(x['rows'])==2076
 assert au['trace_checks']==5760 and au['decision_checks']==184320 and len(x['traces'])==1440 and au['observed_future_grid_violations']==0
 assert len([r for r in d['rows'] if r['split']=='test' and r['pose_geometry']['status']=='refused'])==4
 assert [v['grants']['joint_hull'] for v in s['policies']]==[4728,4728,4727,3157] and [v['grants'] for v in x['policies']]==[2279,2279,0,0]
 assert s['setup']['wire_bytes']==56710 and s['audit_sha256']==sha(P/'audit_sheng.json')
 native=read(P/'native_runtime_sheng.json');parent=ROOT/'results/body_expiry_20261004/native_build_sheng.json';assert native['parent_build_sha256']==sha(parent) and native['binary_sha256']==read(parent)['local_binary_sha256']
 assert diag['total_tilt_violated_frames']==tilt['count']==72 and [v['grants_referencing_tilt_violated_source'] for v in diag['policies']]==[155,155,155,111]
 assert len(tilt['witnesses'])==72 and all(v['norm_lower_num']*1000000>87267*v['norm_lower_den'] for v in tilt['witnesses'])
 for host in ('local','sheng'):
  log=(P/('tests_'+host+'.log')).read_text();assert 'Ran 9 tests' in log and log.rstrip().endswith('OK')
 assert (P/'run_terminal.txt').read_text()=='FINITE_POSE_SUPPORT_COMPLETE\n' and (P/'raw_optimization_terminal.txt').read_text()=='FINITE_RAW_OPTIMIZATION_COMPLETE\n'
 rev=read(E/'tilt_prior_revision.json');assert rev['first_sha256']==sha(E/'tilt_prior_lower_bound_at_first_run.py') and rev['corrected_sha256']==sha(E/'tilt_prior_lower_bound.py');assert (E/'tilt_prior_lower_bound_at_first_run.py').read_text().replace('p=a.results;','p=a.results.resolve();')==(E/'tilt_prior_lower_bound.py').read_text() and 'ValueError' in (P/'tilt_prior_first_run_local.log').read_text()
 if a.freeze:
  sources=sorted(p for p in E.iterdir() if p.is_file())+[ROOT/'research/pose_support_result_20261004.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sources}))
  write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=9,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Finite reused-data unknown-yaw outer support, exact solver, paid strong-baseline comparison and72 any-yaw tilt-prior witnesses. No new risk qualification, unknown inventory, continuous physical/live ego guarantee or MobiCom contribution established.'))
  files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
 for n,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/n)==h,n
 m=read(P/'artifact_manifest.json');assert {str(p.relative_to(ROOT)) for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json'}==set(m['files'])
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
 print(json.dumps(dict(result_files=m['file_count'],total_bytes=m['total_bytes'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
