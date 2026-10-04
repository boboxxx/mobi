#!/usr/bin/env python3
"""Byte closure only; never turn prototype geometry or diagnostics into risk proof."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
REPORT='research/ego_expiry_live_result_20261004.md'
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
 for section in ('sources','inputs'):hashes(f[section])
 for filename in ('compact_freeze.json','portable_freeze.json'):
  supplement=read(E/filename)
  for section in ('sources','inputs'):hashes(supplement[section])
 pre=read(P/'preregistration.json');assert pre['capture_absent_before_run'] and not pre['policy_risk_qualified'] and not pre['recurring_job_created'] and pre['freeze_sha256']==sha(E/'freeze.json')
 assert (P/'terminal.txt').read_text()=='FINITE_PHYSICAL_EGO_EXPIRY_CAPTURE_AND_AUDIT_COMPLETE\n'
 assert read(P/'capture/cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
 start,stop=read(P/'server_start.json'),read(P/'server_stopped.json')
 for key in ('pid','executable','start_time_utc','experiment'):assert start[key]==stop[key]
 assert stop['stopped'] and stop['experiment']==E.name
 assert (P/'audit_local.json').read_bytes()==(P/'audit_sheng.json').read_bytes()
 assert (P/'audit_portable_sheng.json').read_bytes()==(P/'audit_sheng.json').read_bytes()
 assert (P/'compact_local.json').read_bytes()==(P/'compact_sheng.json').read_bytes()
 compact=read(P/'compact_sheng.json');assert compact['matched_source_observations']==1920 and compact['original_deadline_gates_verified']==1179 and compact['all_source_expiry_and_domain_semantics_preserved'] and not compact['old_driving_or_timing_rewritten'] and not compact['new_risk_or_radio_or_driving_qualified']
 assert compact['cases_sha256']==sha(P/'compact_cases.jsonl') and compact['freeze_sha256']==sha(E/'compact_freeze.json')
 diagnostic=read(P/'float_replay_diagnostic.json');assert diagnostic['mismatch_count']==102 and diagnostic['max_absolute_difference']<1e-15 and diagnostic['initial_failure_log_sha256']==sha(P/'audit_local_initial_failure.log')
 old=(E/'audit.py').read_text();new=(E/'audit_portable.py').read_text();assert old.replace("assert throttle==row['requested_throttle'] and brake==row['requested_brake']","assert abs(throttle-row['requested_throttle'])<=1e-15 and abs(brake-row['requested_brake'])<=1e-15")==new
 audit=read(P/'audit_sheng.json');assert audit['planned']==12 and not audit['goal_complete'] and not audit['deployment_authorizations'] and audit['freeze_sha256']==sha(E/'freeze.json') and audit['outcomes_sha256']==sha(P/'capture/outcomes.json')
 outcomes=read(P/'capture/outcomes.json');assert len(outcomes)==12 and [v['request'] for v in outcomes]==read(E/'plan.json')
 for row in outcomes:
  q=Path(row['file']);assert not q.is_absolute() and '..' not in q.parts
  p=P/'capture'/q;assert sha(p)==row['sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==row['logical_bytes'] and hashlib.sha256(b).hexdigest()==row['logical_sha256']
 for name in ('tests_pre_freeze_local.log','tests_sheng.log'):
  t=(P/name).read_text();assert 'Ran 3 tests' in t and t.rstrip().endswith('OK')
 if a.prepare:
  sources=dict(f['sources'])
  for p in E.iterdir():
   if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
  sources[REPORT]=sha(ROOT/REPORT)
  write(P/'publication_source_manifest.json',dict(sources=sources,inputs=f['inputs'],scope='Pre-capture source closure plus post-result packaging/report; no experimental source retuning.'))
  files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()};assert all(v['bytes']<100*1024*1024 for v in files.values())
  write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),exclusions=sorted(EXCLUDE)))
 pub=read(P/'publication_source_manifest.json')
 for section in ('sources','inputs'):hashes(pub[section])
 m=read(P/'artifact_manifest.json');assert set(artifacts())==set(m['files']) and m['file_count']==len(m['files']) and m['total_bytes']==sum(v['bytes'] for v in m['files'].values())
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes']
 out=dict(files=m['file_count'],bytes=m['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),audit_sha256=sha(P/'audit_sheng.json'),captured=audit['captured'],source_scans=audit['source_scans'],decisions=audit['decisions'],diagnostic_violations=audit['violations'],byte_closure_valid=True,finite_prototype_complete=True,scene_or_ego_policy_or_radio_qualified=False,server_stopped=True,goal_complete=False)
 if a.out:write(a.out,out)
 print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
