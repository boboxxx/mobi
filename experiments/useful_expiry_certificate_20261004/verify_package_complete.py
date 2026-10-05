#!/usr/bin/env python3
"""Publication closure added after core freeze; no changes to policy or capture."""
import argparse,gzip,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=R/'results'/E.name
REPORT='research/useful_expiry_certificate_result_20261004.md';EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
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

def artifacts():
 return {str(p.relative_to(R)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE and not (len(p.relative_to(P).parts)>1 and p.relative_to(P).parts[0] in ('certification_capture','test_capture') and p.relative_to(P).parts[1] in ('clouds','packets'))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 f=read(E/'freeze.json')
 for section in ('sources','inputs'):hashes(f[section])
 assert (P/'input_verification_local.json').read_bytes()==(P/'input_verification_sheng.json').read_bytes()
 iv=read(P/'input_verification_sheng.json');assert iv['all_input_bytes_verified'] and iv['freeze_sha256']==sha(E/'freeze.json') and set(iv['verified_inputs'])==set(f['inputs'])
 for name,x in iv['verified_inputs'].items():assert x['sha256']==f['inputs'][name] and x['bytes']==(R/name).stat().st_size
 fresh=read(P/'input_restore_fresh_local.json');assert fresh['freeze_sha256']==sha(E/'freeze.json') and fresh['helper_sha256']==sha(E/'restore_inputs_complete.py') and fresh['all_60_input_bytes_match'] and fresh['repeated_verification_did_not_replace_inputs'] and fresh['isolated_fresh_tree'] and len(fresh['logical_files_restored_from_committed_gzip'])==4
 pre=read(P/'preregistration.json');assert pre['freeze_sha256']==sha(E/'freeze.json')
 assert (P/'terminal.txt').read_text()=='FINITE_USEFUL_EXPIRY_CERTIFICATION_AND_TEST_COMPLETE\n'
 start,stop=read(P/'server_start.json'),read(P/'server_stopped.json')
 for k in ('pid','executable','start_time_utc','experiment'):assert start[k]==stop[k]
 assert stop['stopped'] and stop['experiment']==E.name
 storage=read(P/'storage_manifest.json');raw={}
 for name,b in storage['bundles'].items():
  q=P/name;assert q.is_file() and q.stat().st_size==b['bytes'] and sha(q)==b['sha256'];assert not set(raw).intersection(b['members']);raw.update(b['members'])
 assert len(raw)==storage['raw_files'] and sum(v['bytes'] for v in raw.values())==storage['raw_bytes']
 assert (P/'storage_verification_local.json').read_bytes()==(P/'storage_verification_sheng.json').read_bytes()
 sv=read(P/'storage_verification_sheng.json');assert sv['all_member_bytes_verified'] and sv['storage_manifest_sha256']==sha(P/'storage_manifest.json') and sv['raw_files']==len(raw)
 scans=decisions=0;used=set()
 for split,n in (('certification',540),('test',72)):
  assert (P/('audit_'+split+'_local.json')).read_bytes()==(P/('audit_'+split+'_sheng.json')).read_bytes()
  au=read(P/('audit_'+split+'_sheng.json'));capture=P/(split+'_capture');assert au['planned']==n and au['split']==split and au['freeze_sha256']==sha(E/'freeze.json') and au['outcomes_sha256']==sha(capture/'outcomes.json') and au['deployment_authorizations']==0 and not au['goal_complete']
  assert read(capture/'cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
  outcomes=read(capture/'outcomes.json');assert len(outcomes)==n and [o['request'] for o in outcomes]==[v for v in read(E/'plan.json') if v['split']==split]
  for o in outcomes:
   q=Path(o['file']);assert not q.is_absolute() and '..' not in q.parts;ep=capture/q;assert sha(ep)==o['sha256'];b=gzip.decompress(ep.read_bytes());assert len(b)==o['logical_bytes'] and hashlib.sha256(b).hexdigest()==o['logical_sha256'];d=json.loads(b);assert d['request']==o['request']
   for s in d['sources']:
    for sub,key,hkey in [('clouds','cloud','cloud_sha256'),('packets','packet','packet_sha256')]:
     name=split+'_capture/'+sub+'/'+s[key];assert name in raw and raw[name]['sha256']==s[hkey] and name not in used;used.add(name)
     if sub=='packets':assert raw[name]['bytes']==s['wire_bytes']
  scans+=au['source_scans'];decisions+=au['decisions']
 for name in ('certificate','summary'):assert (P/(name+'_local.json')).read_bytes()==(P/(name+'_sheng.json')).read_bytes()
 c=read(P/'policy_frozen.json');exact=read(P/'certificate_sheng.json');summary=read(P/'summary_sheng.json')
 assert c['certification_complete'] and c['test_capture_absent_when_frozen'] and c['binary_tests']==6 and c['zero_failure_accepted_required']==94 and not c['production_road_authorized'] and not c['goal_complete']
 assert exact['all_progress_labels_independently_checked'] and exact['joint_confidence_lower']==[19,20] and exact['policy_sha256']==sha(P/'policy_frozen.json')==summary['policy_sha256']
 assert summary['test_audit_sha256']==sha(P/'audit_test_sheng.json') and len(summary['cells'])==3 and sum(x['planned'] for x in summary['cells'])==72
 for name in ('tests_pre_freeze_local.log','tests_sheng.log'):
  t=(P/name).read_text();assert 'Ran 6 tests' in t and t.rstrip().endswith('OK')
 mf=read(E/'matched_freeze.json')
 for section in ('sources','inputs'):hashes(mf[section])
 mp=read(P/'matched_preregistration.json');assert mp['test_capture_absent'] and mp['policy_certificate_absent'] and mp['matched_output_absent'] and mp['freeze_sha256']==sha(E/'matched_freeze.json')
 assert (P/'matched_local.json').read_bytes()==(P/'matched_sheng.json').read_bytes()
 matched=read(P/'matched_sheng.json');ta=read(P/'audit_test_sheng.json');assert matched['matched_freeze_sha256']==sha(E/'matched_freeze.json') and matched['freeze_sha256']==sha(E/'freeze.json') and matched['paired_sources']==ta['source_scans'] and matched['planned_episodes']==72 and matched['complete_episodes']==ta['captured'] and matched['matched_cached_drive_queries']+matched['missing_cached_drive_queries']==ta['captured']*60 and matched['actual_method_packets_reproduced'] and matched['test_audit_sha256']==sha(P/'audit_test_sheng.json')
 sync=R/'results/receiver_source_sync_20261005'
 assert (sync/'verification_local.json').read_bytes()==(sync/'verification_sheng.json').read_bytes()
 cr=read(sync/'verification_sheng.json');assert cr['exactly_one_trailing_LF_difference'] and cr['ast_equal'] and cr['original_executed_source_preserved'] and cr['manifest_sha256']==sha(sync/'manifest.json')
 assert (sync/'original_recover_cleanup_sheng.py').read_bytes()==(sync/'canonical_recover_cleanup.py').read_bytes()+b'\n'
 for name,h in read(sync/'manifest.json')['files'].items():assert sha(R/name)==h
 fi=read(P/'figure_inputs.json');assert fi['summary_sha256']==sha(P/'summary_local.json') and fi['figure_sha256']==sha(P/'all_methods.png')
 if a.prepare:
  src=dict(f['sources']);src.update({str(p.relative_to(R)):sha(p) for p in E.iterdir() if p.is_file()});src[REPORT]=sha(R/REPORT);src['research/evidence_expiry_argument_20261004.md']=sha(R/'research/evidence_expiry_argument_20261004.md');src['research/compact_expiry_bound_20261004.md']=sha(R/'research/compact_expiry_bound_20261004.md');src['research/useful_expiry_literature_addendum_20261004.md']=sha(R/'research/useful_expiry_literature_addendum_20261004.md')
  for q in sync.iterdir():
   if q.is_file():src[str(q.relative_to(R))]=sha(q)
  src['research/receiver_source_sync_20261005.md']=sha(R/'research/receiver_source_sync_20261005.md')
  write(P/'publication_source_manifest.json',dict(sources=src,inputs=f['inputs'],scope='Core and complete plan frozen before captures. Descriptive plot/report and archive publication closure added separately, without policy changes.'))
  files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()};assert all(v['bytes']<100*1024**2 for v in files.values());write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),exclusions=sorted(EXCLUDE),raw_storage='Lossless observations/*.tar.xz; original raw files not duplicated in Git.'))
 for section in ('sources','inputs'):hashes(read(P/'publication_source_manifest.json')[section])
 m=read(P/'artifact_manifest.json');assert set(artifacts())==set(m['files']) and len(m['files'])==m['file_count'] and sum(v['bytes'] for v in m['files'].values())==m['total_bytes']
 for n,v in m['files'].items():assert sha(R/n)==v['sha256'] and (R/n).stat().st_size==v['bytes']
 write(a.out,dict(artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),files=m['file_count'],bytes=m['total_bytes'],raw_files=storage['raw_files'],raw_bytes=storage['raw_bytes'],source_scans=scans,decisions=decisions,jointly_accepted_methods=sum(x['accepted'] for x in c['methods'].values()),policy_sha256=sha(P/'policy_frozen.json'),all_published_bytes_verified=True,both_host_full_replays_identical=True,server_stopped=True,production_or_radio_or_unknown_actor_qualified=False,goal_complete=False))
 print('USEFUL_EXPIRY_PACKAGE_CLOSURE_OK')
if __name__=='__main__':main()
