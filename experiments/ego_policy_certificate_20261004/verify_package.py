#!/usr/bin/env python3
"""Verify every published finite-batch byte and both independent host replays."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
REPORT='research/ego_policy_certificate_result_20261004.md'
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
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
  q=Path(n);assert not q.is_absolute() and '..' not in q.parts and sha(ROOT/n)==h,n

def artifacts():return {str(p.relative_to(ROOT)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 f=read(E/'freeze.json');post=read(E/'analysis_freeze.json')
 for v in (f,post):
  for section in ('sources','inputs'):hashes(v[section])
 pre=read(P/'preregistration.json');assert pre['certification_capture_absent_before_run'] and pre['test_capture_absent_before_run'] and pre['policy_certificate_absent_before_run'] and not pre['policy_risk_qualified_before_run'] and not pre['recurring_job_created'] and pre['planned_certification']==540 and pre['planned_test']==72 and pre['freeze_sha256']==sha(E/'freeze.json')
 apr=read(P/'analysis_preregistration.json');assert apr['test_capture_absent'] and apr['policy_certificate_absent'] and apr['summary_absent'] and apr['freeze_sha256']==sha(E/'analysis_freeze.json')
 assert (P/'terminal.txt').read_text()=='FINITE_WHOLE_EGO_CERTIFICATION_AND_TEST_COMPLETE\n'
 start,stop=read(P/'server_start.json'),read(P/'server_stopped.json')
 for k in ('pid','executable','start_time_utc','experiment'):assert start[k]==stop[k]
 assert stop['stopped'] and stop['experiment']==E.name
 total_scans=total_decisions=0
 for split,n in (('certification',540),('test',72)):
  prefix='audit_'+split;assert (P/(prefix+'_local.json')).read_bytes()==(P/(prefix+'_sheng.json')).read_bytes()
  au=read(P/(prefix+'_sheng.json'));capture=P/(split+'_capture');assert au['planned']==n and au['split']==split and au['freeze_sha256']==sha(E/'freeze.json') and au['outcomes_sha256']==sha(capture/'outcomes.json') and not au['goal_complete'] and au['deployment_authorizations']==0
  assert read(capture/'cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
  outcomes=read(capture/'outcomes.json');assert len(outcomes)==n and [o['request'] for o in outcomes]==[v for v in read(E/'plan.json') if v['split']==split]
  labels={v['id']:v for v in au['risk_labels']};assert len(labels)==n
  for o in outcomes:
   q=Path(o['file']);assert not q.is_absolute() and '..' not in q.parts
   ep=capture/q;assert sha(ep)==o['sha256'];b=gzip.decompress(ep.read_bytes());assert len(b)==o['logical_bytes'] and hashlib.sha256(b).hexdigest()==o['logical_sha256'];d=json.loads(b)
   assert d['request']==o['request']
   if o['status']!='captured':
    selected=any(v['engineering_go'] for v in d['attempts']);assert labels[o['request']['id']]['selected']==selected and labels[o['request']['id']]['failed']==selected
   for s in d['sources']:
    assert sha(capture/'clouds'/s['cloud'])==s['cloud_sha256'];assert sha(capture/'packets'/s['packet'])==s['packet_sha256'] and (capture/'packets'/s['packet']).stat().st_size==s['wire_bytes']
  total_scans+=au['source_scans'];total_decisions+=au['decisions']
 for n in ('certificate','summary'):assert (P/(n+'_local.json')).read_bytes()==(P/(n+'_sheng.json')).read_bytes()
 cert=read(P/'certificate_sheng.json');policy=read(P/'policy_frozen.json');summary=read(P/'summary_sheng.json')
 assert policy['certification_complete'] and policy['test_capture_absent_when_frozen'] and not policy['production_road_authorized'] and policy['zero_failure_accepted_required']==80 and policy['binary_tests']==3 and not policy['goal_complete']
 assert cert['policy_sha256']==summary['policy_sha256']==sha(P/'policy_frozen.json') and cert['joint_confidence_lower']==[19,20] and not cert['road_or_radio_qualified']
 assert summary['test_audit_sha256']==sha(P/'audit_test_sheng.json') and len(summary['cells'])==3 and sum(v['planned'] for v in summary['cells'])==72
 for log in ('tests_pre_freeze_local.log','tests_sheng.log'):
  t=(P/log).read_text();assert 'Ran 3 tests' in t and t.rstrip().endswith('OK')
 fig=read(P/'figure_inputs.json');hashes(fig['input_sha256']);assert sha(P/'all_methods.png')==fig['figure_sha256'] and fig['all_methods']==['function','deadline','cone']
 if a.prepare:
  sources=dict(f['sources'])
  for p in E.iterdir():
   if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
  sources[REPORT]=sha(ROOT/REPORT);write(P/'publication_source_manifest.json',dict(sources=sources,inputs=f['inputs'],scope='Pre-capture core, pre-held-out-analysis helpers, post-result report and packaging; no retuning.'))
  files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()};assert all(v['bytes']<100*1024*1024 for v in files.values())
  write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),exclusions=sorted(EXCLUDE)))
 for section in ('sources','inputs'):hashes(read(P/'publication_source_manifest.json')[section])
 manifest=read(P/'artifact_manifest.json');assert set(artifacts())==set(manifest['files']) and manifest['file_count']==len(manifest['files']) and manifest['total_bytes']==sum(v['bytes'] for v in manifest['files'].values())
 for n,v in manifest['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes']
 result=dict(files=manifest['file_count'],bytes=manifest['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),policy_sha256=sha(P/'policy_frozen.json'),certificate_sha256=sha(P/'certificate_sheng.json'),summary_sha256=sha(P/'summary_sheng.json'),source_scans=total_scans,decisions=total_decisions,conditional_certificate_methods=sum(v['accepted'] for v in policy['methods'].values()),byte_closure_valid=True,finite_prototype_complete=True,road_or_radio_or_unseen_actor_qualified=False,server_stopped=True,goal_complete=False)
 write(a.out,result);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
