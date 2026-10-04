#!/usr/bin/env python3
"""Complete finite diagnostic byte closure; not a safety certificate."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
REPORT='research/near_expiry_live_result_20261004.md'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
 assert not p.exists(),p
 p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def hashes(mapping):
 for n,h in mapping.items():
  q=Path(n);assert not q.is_absolute() and '..' not in q.parts and sha(ROOT/n)==h,n
def artifacts():return {str(p.relative_to(ROOT)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path);a=ap.parse_args();f=read(E/'freeze.json')
 for sec in ('sources','inputs'):hashes(f[sec])
 supplement=read(E/'import_freeze.json')
 for sec in ('sources','inputs'):hashes(supplement[sec])
 old=(E/'analyze.py').read_text();new=(E/'analyze_importsafe.py').read_text();assert old.replace('import audit as A',"import importlib.util\nspec=importlib.util.spec_from_file_location('near_expiry_fixed_audit',Path(__file__).resolve().parent/'audit.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)")==new
 assert (P/'analysis_sheng.log').read_bytes()==(P/'analysis_initial_failure.log').read_bytes()
 assert 'AttributeError' in (P/'analysis_initial_failure.log').read_text()
 for sec in ('sources','inputs'):hashes(read(E/'analysis_freeze.json')[sec])
 previous=(E/'analyze_importsafe.py').read_text();complete=(E/'analyze_complete.py').read_text();assert previous.replace('import runtime as R','import runtime as R\nfrom query_kernel import horizon').replace('R.horizon(','horizon(')==complete
 assert (P/'analysis_corrected_sheng.log').read_bytes()==(P/'analysis_second_failure.log').read_bytes()
 assert 'AttributeError' in (P/'analysis_second_failure.log').read_text()
 pre=read(P/'preregistration.json');assert pre['capture_absent_before_run'] and not pre['policy_risk_qualified'] and not pre['recurring_job_created'] and pre['planned']==18 and pre['freeze_sha256']==sha(E/'freeze.json')
 assert (P/'terminal.txt').read_text()=='FINITE_NEAR_HAZARD_CAPTURE_AND_AUDIT_COMPLETE\n'
 assert read(P/'capture/cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
 start,stop=read(P/'server_start.json'),read(P/'server_stopped.json')
 for k in ('pid','executable','start_time_utc','experiment'):assert start[k]==stop[k]
 assert stop['stopped'] and stop['experiment']==E.name
 for n in ('audit','analysis'):assert (P/(n+'_local.json')).read_bytes()==(P/(n+'_sheng.json')).read_bytes()
 assert (P/'timing_floor_local.json').read_bytes()==(P/'timing_floor_sheng.json').read_bytes()
 timing=read(P/'timing_floor_sheng.json');assert timing['same_first_decode_tick']==2517 and timing['different_first_decode_tick']==3 and timing['unresolved']==0 and not timing['actual_driving_rewritten']
 for n,fname in [('analysis_preregistration.json','import_freeze.json'),('analysis_complete_preregistration.json','analysis_freeze.json')]:
  pr=read(P/n);assert pr['first_successful_analysis_absent'] and not pr['capture_replaced'] and pr['freeze_sha256']==sha(E/fname)
 audit=read(P/'audit_sheng.json');analysis=read(P/'analysis_sheng.json');assert audit['planned']==analysis['planned']==18 and not audit['goal_complete'] and not analysis['goal_complete'] and not audit['deployment_authorizations']
 for v in (audit,analysis):assert v['freeze_sha256']==sha(E/'freeze.json') and v['outcomes_sha256']==sha(P/'capture/outcomes.json')
 assert analysis['source_queries']==audit['source_scans'] and analysis['captured']==audit['captured']
 outcomes=read(P/'capture/outcomes.json');assert len(outcomes)==18 and [v['request'] for v in outcomes]==read(E/'plan.json')
 for row in outcomes:
  q=Path(row['file']);assert not q.is_absolute() and '..' not in q.parts
  p=P/'capture'/q;assert sha(p)==row['sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==row['logical_bytes'] and hashlib.sha256(b).hexdigest()==row['logical_sha256']
 for n in ('tests_pre_capture_local.log','tests_sheng.log'):
  t=(P/n).read_text();assert 'Ran 3 tests' in t and t.rstrip().endswith('OK')
 fig=read(P/'figure_inputs.json');hashes(fig['input_sha256']);assert len(fig['input_sha256'])==18
 if a.prepare:
  sources=dict(f['sources'])
  for p in E.iterdir():
   if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
  sources[REPORT]=sha(ROOT/REPORT)
  sources['research/expiry_motion_prior_work_20261004.md']=sha(ROOT/'research/expiry_motion_prior_work_20261004.md')
  write(P/'publication_source_manifest.json',dict(sources=sources,inputs=f['inputs'],scope='Pre-capture core plus post-result report/packaging/plot; no retuning.'))
  files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()};assert all(v['bytes']<100*1024*1024 for v in files.values())
  write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),exclusions=sorted(EXCLUDE)))
 for sec in ('sources','inputs'):hashes(read(P/'publication_source_manifest.json')[sec])
 m=read(P/'artifact_manifest.json');assert set(artifacts())==set(m['files']) and m['file_count']==len(m['files']) and m['total_bytes']==sum(v['bytes'] for v in m['files'].values())
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes']
 out=dict(files=m['file_count'],bytes=m['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),audit_sha256=sha(P/'audit_sheng.json'),analysis_sha256=sha(P/'analysis_sheng.json'),captured=audit['captured'],source_scans=audit['source_scans'],decisions=audit['decisions'],diagnostic_violations=audit['violations'],byte_closure_valid=True,finite_prototype_complete=True,policy_or_radio_or_unseen_actor_qualified=False,server_stopped=True,goal_complete=False)
 if a.out:write(a.out,out)
 print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
