#!/usr/bin/env python3
"""Post-run closure and exhaustive plan/policy/publication scope verification."""
import argparse,hashlib,itertools,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();subprocess.run([sys.executable,str(E/'prepare_archive.py')],check=True);d=read(P/'analysis_sheng.json');au=read(P/'audit_sheng.json');s=read(P/'summary_sheng.json');lease=read(P/'lease_baseline_sheng.json');la=read(P/'lease_audit_sheng.json');plan=read(E/'plan.json');eps=read(P/'capture/episodes.json');records=read(P/'capture/record.json');manifest=read(P/'capture/manifest.json');pairs=[]
 for stem,source,target in [('audit_v2','audit_portable_v2.py','analysis_sheng.json'),('summary_normalized','normalize_summary.py','analysis_sheng.json'),('lease_audit','audit_lease_baseline.py','lease_baseline_sheng.json'),('comparison','compare_results.py','lease_baseline_sheng.json'),('diagnostic','failure_diagnostic.py','analysis_sheng.json')]:
  assert (P/(stem+'_local.json')).read_bytes()==(P/(stem+'_sheng.json')).read_bytes(),stem
  v=read(P/(stem+'_sheng.json'));assert v['source_sha256']==sha(E/source) and v['analysis_sha256']==sha(P/target);pairs.append(dict(stem=stem,sha256=sha(P/(stem+'_sheng.json'))))
 v2=read(P/'audit_v2_sheng.json');assert v2['coordinate_rounding_checks']==len(d['rows'])
 original=dict(au);replayed=dict(v2)
 for key in ('source_sha256','coordinate_rounding_checks','maximum_affine_error_um'):original.pop(key,None);replayed.pop(key,None)
 assert original==replayed
 assert au['source_sha256']==sha(E/'audit_portable.py')
 assert read(P/'summary_normalized_sheng.json')['raw_summarizer_source_sha256']==sha(E/'summarize.py')
 # Preserve raw summaries and verify that only documented presentation fields differ.
 raw_a=read(P/'summary_local.json');raw_b=read(P/'summary_sheng.json');presentation_diff=[]
 for ca,cb in zip(raw_a['classes'],raw_b['classes']):
  for key in ('single_class_risk_upper95','simultaneous_six_class_risk_upper95'):
   if ca[key]!=cb[key]:presentation_diff.append(dict(blueprint=ca['blueprint'],field=key,local=ca[key],sheng=cb[key]));assert abs(ca[key]-cb[key])<2e-15
   ca[key]=round(ca[key],15);cb[key]=round(cb[key],15)
 assert raw_a==raw_b
 repair=read(P/'audit_repair_receipt.json');assert repair['original_source_sha256']==sha(E/'audit.py') and repair['repaired_source_sha256']==sha(E/'audit_portable.py') and repair['first_failure_log_sha256']==sha(P/'audit_sheng_first_failure.log') and repair['model_plan_registry_geometry_wire_fifo_unchanged']
 native=read(P/'native_runtime_sheng.json');assert native['native_sha256']==read(ROOT/'results/body_expiry_20261004/native_build_sheng.json')['local_binary_sha256'] and native['build_receipt_sha256']==sha(ROOT/'results/body_expiry_20261004/native_build_sheng.json')
 assert (P/'smoke_local_before_capture.json').read_bytes()==(P/'smoke_sheng_before_capture.json').read_bytes()
 for f in (read(E/'freeze.json'),read(E/'lease_baseline_freeze.json')):
  for section in ('sources','inputs'):
   for n,h in f.get(section,{}).items():assert sha(ROOT/n)==h,n
 assert read(E/'lease_baseline_freeze.json')['primary_freeze_sha256']==sha(E/'freeze.json') and d['source_hashes']==read(E/'freeze.json')['sources']
 for n,h in d['input_hashes'].items():assert sha(ROOT/n)==h,n
 assert [e['episode'] for e in eps]==plan and len(plan)==930;assert manifest['episodes']==930 and manifest['frames']==au['frames']==len(records)==len(d['rows']) and manifest['captured_episodes']==sum(e['status']=='captured' for e in eps)
 assert manifest['stored_rays']==sum(r['points'] for r in records) and manifest['original_reported_rays']==sum(r['original_points'] for r in records)
 assert manifest['source_sha256']==sha(E/'capture.py') and manifest['plan_sha256']==sha(E/'plan.json') and manifest['protocol_sha256']==sha(E/'PROTOCOL.md')
 byep={e['episode']['id']:[] for e in eps}
 for r in records:byep[r['episode_id']].append(r)
 for e in eps:
  rr=byep[e['episode']['id']]
  if e['status']=='captured':assert len(rr)==6 and {(r['step'],r['layout']) for r in rr}==set(itertools.product((0,5,10),(0,1))) and len(e['trajectory'])==21 and [v['step'] for v in e['trajectory']]==list(range(21))
  else:assert not rr
 captured={str(P.relative_to(ROOT)/'capture'/r['cloud_file']) for r in records};assert set(d['input_hashes'])==captured and captured=={str(p.relative_to(ROOT)) for p in (P/'capture/clouds').glob('*.npz')}
 for f in (read(P/'preregistration.json'),read(P/'lease_baseline_registered_during_capture.json')):assert not f.get('goal_complete',False)
 pr=read(P/'preregistration.json');assert pr['published_source_commit']=='a10acd54abdfb9c36e517b0765adf58c5041ca92' and pr['freeze_sha256']==sha(E/'freeze.json') and pr['fresh_capture_directory_absent'] and pr['smoke_cross_host_equal']
 reg=read(P/'lease_baseline_registered_during_capture.json');assert reg['freeze_sha256']==sha(E/'lease_baseline_freeze.json') and reg['primary_freeze_sha256']==sha(E/'freeze.json') and reg['primary_calibration_output_absent'] and reg['primary_analysis_absent']
 receipt=read(P/'calibration_frozen.json');assert d['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and receipt['registry']==d['registry'] and set(receipt['input_hashes'])=={str(P.relative_to(ROOT)/'capture'/r['cloud_file']) for r in records if r['split']=='calibration'}
 planned={e['episode']['id']:e for e in eps if e['episode']['split']=='test'};assert len(planned)==360
 expected={(ep,method,rate,startup) for ep,method,rate,startup in itertools.product(planned,('sphere_hull','pose_hull','joint_hull','joint_raw'),(20000000,2000000),('warm','cold'))}
 got={(t['episode_id'],t['method'],t['rate'],t['startup']) for t in d['traces']};assert got==expected and len(d['traces'])==5760 and au['trace_checks']==5760 and au['decision_checks']==184320
 for t in d['traces']:assert t['blueprint']==planned[t['episode_id']]['episode']['blueprint'] and t['capture_status']==planned[t['episode_id']]['status'] and t['scheduled_queries']==len(t['decisions'])==32
 lexpected={(ep,reg,rate,startup) for ep,reg,rate,startup in itertools.product(planned,('full','minimal'),(20000000,2000000),('warm','cold'))};lgot={(t['episode_id'],t['registration'],t['rate'],t['startup']) for t in lease['traces']};assert lgot==lexpected and len(lease['traces'])==la['trace_checks']==2880 and la['decision_checks']==92160
 for t in lease['traces']:assert t['method']=='lease' and t['blueprint']==planned[t['episode_id']]['episode']['blueprint'] and t['capture_status']==planned[t['episode_id']]['status'] and t['scheduled_queries']==len(t['decisions'])==32
 assert la['primary_audit_sha256']==lease['primary_audit_sha256']==sha(P/'audit_sheng.json') and lease['primary_analysis_sha256']==sha(P/'analysis_sheng.json') and lease['freeze_sha256']==sha(E/'lease_baseline_freeze.json') and s['audit_sha256']==sha(P/'audit_sheng.json')
 for host in ('local','sheng'):
  for n,count in [('tests_'+host+'.log',5),('tests_inherited_'+host+'.log',9)]:log=(P/n).read_text();assert ('Ran %d tests'%count) in log and log.rstrip().endswith('OK')
 for name,expected in [('capture_terminal.txt','CAPTURE_TERMINAL_SUCCESS\n'),('run_terminal.txt','FINITE_PROSPECTIVE_SHAPE_COMPLETE\n'),('lease_terminal.txt','FINITE_LEASE_BASELINE_COMPLETE\n')]:assert (P/name).read_text()==expected
 stopped=read(P/'server_stopped.json');started=read(P/'server_started.json');assert stopped['stopped'] and stopped['pid']==started['pid'] and stopped['executable']==started['executable'] and stopped['experiment']==started['experiment']=='prospective_shape_20261004'
 if a.freeze:
  sources=sorted(p for p in E.iterdir() if p.is_file())+[ROOT/'research/prospective_shape_result_20261004.md',ROOT/'README.md',ROOT/'research/PROJECT_STATUS.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sources}))
  write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=dict(primary_membership=3,lease_followup=2,inherited_geometry=9),source_manifest_sha256=sha(P/'publication_source_manifest.json'),capture_plan_episodes=930,raw_summary_presentation_differences=presentation_diff,lossless_analysis_archive=read(P/'archive_representation.json'),full_goal_complete=False,scope='Fresh fixed-law joint current-center qualification and paid four-policy plus strong direct-deadline comparison; no unknown inventory, continuous physical/live ego guarantee or distinct MobiCom contribution established.'))
  files=sorted(p for p in P.rglob('*') if p.is_file() and p.name not in ('artifact_manifest.json','analysis_sheng.json'));write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
 for n,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/n)==h,n
 m=read(P/'artifact_manifest.json');assert set(m['files'])=={str(p.relative_to(ROOT)) for p in P.rglob('*') if p.is_file() and p.name not in ('artifact_manifest.json','analysis_sheng.json')}
 for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
 print(json.dumps(dict(result_files=m['file_count'],total_bytes=m['total_bytes'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
