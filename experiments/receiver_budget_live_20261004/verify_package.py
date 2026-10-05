#!/usr/bin/env python3
"""Post-result closure, retaining the original cleanup-copy failure."""
import argparse,gzip,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=R/'results'/E.name
REPORT='research/receiver_budget_live_result_20261004.md';EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
 assert not p.exists(),p
 p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def hashes(d):
 for n,h in d.items():
  q=Path(n);assert not q.is_absolute() and '..' not in q.parts and sha(R/q)==h,n

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 f=read(E/'freeze.json')
 for section in ('sources','inputs'):hashes(f[section])
 pre=read(P/'preregistration.json');assert pre['capture_absent_before_run'] and pre['old_results_used_for_development'] and not pre['old_risk_certificate_transferred'] and not pre['recurring_job_created'] and pre['planned']==36 and pre['freeze_sha256']==sha(E/'freeze.json')
 assert (P/'terminal.txt').read_text()=='FINITE_RECEIVER_BUDGET_CAPTURE_AND_AUDIT_COMPLETE\n'
 assert (P/'audit_local.json').read_bytes()==(P/'audit_sheng.json').read_bytes()
 assert (P/'summary_local.json').read_bytes()==(P/'summary_sheng.json').read_bytes()
 au=read(P/'audit_sheng.json');assert au['planned']==au['captured']==36 and au['source_scans']==900 and au['decisions']==3600 and au['deployment_authorizations']==0 and not au['goal_complete']
 assert au['freeze_sha256']==sha(E/'freeze.json') and au['outcomes_sha256']==sha(P/'capture/outcomes.json')
 outcomes=read(P/'capture/outcomes.json');plan=read(E/'plan.json');assert [x['request'] for x in outcomes]==plan
 assert len(outcomes)==len(au['episodes'])==36
 n=0
 for o in outcomes:
  q=Path(o['file']);assert not q.is_absolute() and '..' not in q.parts;p=P/'capture'/q;assert sha(p)==o['sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==o['logical_bytes'] and hashlib.sha256(raw).hexdigest()==o['logical_sha256'];d=json.loads(raw);assert d['request']==o['request']
  for s in d['sources']:
   assert sha(P/'capture/clouds'/s['cloud'])==s['cloud_sha256'];pk=P/'capture/packets'/s['packet'];assert sha(pk)==s['packet_sha256'] and pk.stat().st_size==s['wire_bytes'];n+=1
 assert n==900 and read(P/'capture/cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
 start,stop=read(P/'server_start.json'),read(P/'server_stopped.json')
 for k in ('pid','executable','start_time_utc','experiment'):assert start[k]==stop[k]
 assert stop['stopped'] and stop['experiment']==E.name
 recovery=read(P/'cleanup_copy_recovery.json');assert recovery['already_stopped'] and recovery['no_process_restarted'] and recovery['no_recapture'] and recovery['owned_pid']==start['pid'];assert recovery['original_stop_log_sha256']==sha(P/'server_stop.log')==recovery['recovered_receipt_sha256']==sha(P/'server_stopped.json');assert recovery['server_start_sha256']==sha(P/'server_start.json')
 assert (P/'cleanup_copy_failure.txt').stat().st_size>0
 for name in ('tests_pre_freeze_local.log','tests_sheng.log'):
  t=(P/name).read_text();assert 'Ran 3 tests' in t and t.rstrip().endswith('OK')
 summary=read(P/'summary_local.json');assert summary['audit_sha256']==sha(P/'audit_sheng.json') and len(summary['episodes'])==36 and not summary['joint_risk_certificate']
 fi=read(P/'figure_inputs.json');assert fi['all_cells']==36 and fi['summary_sha256']==sha(P/'summary_local.json') and fi['figure_sha256']==sha(P/'receiver_budget_all_cells.png')
 files={str(p.relative_to(R)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE}
 if a.prepare:
  src=dict(f['sources']);src.update({str(p.relative_to(R)):sha(p) for p in E.iterdir() if p.is_file()});src[REPORT]=sha(R/REPORT)
  write(P/'publication_source_manifest.json',dict(sources=src,inputs=f['inputs'],scope='Frozen core preceded observations. Cleanup receipt recovery, complete descriptive summary, figure, report and packaging followed observations. No retuning.'))
  files[str((P/'publication_source_manifest.json').relative_to(R))]=P/'publication_source_manifest.json'
  members={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in files.items()};assert all(v['bytes']<100*1024**2 for v in members.values());write(P/'artifact_manifest.json',dict(files=members,file_count=len(members),total_bytes=sum(v['bytes'] for v in members.values()),exclusions=sorted(EXCLUDE)))
 for section in ('sources','inputs'):hashes(read(P/'publication_source_manifest.json')[section])
 m=read(P/'artifact_manifest.json');assert set(files)==set(m['files']) and m['file_count']==len(files)
 for n,v in m['files'].items():assert sha(R/n)==v['sha256'] and (R/n).stat().st_size==v['bytes']
 write(a.out,dict(artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),files=m['file_count'],bytes=m['total_bytes'],all_36_cases_preserved=True,source_scans=900,decisions=3600,both_host_replays_identical=True,owner_process_stopped=True,original_copy_failure_preserved=True,development_diagnosis_only=True,production_or_joint_risk_qualified=False,goal_complete=False))
 print('PACKAGE_CLOSURE_OK')
if __name__=='__main__':main()
