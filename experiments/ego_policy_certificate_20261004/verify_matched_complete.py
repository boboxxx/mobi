#!/usr/bin/env python3
"""Cross-check the complete preregistered same-input diagnostic denominators."""
import argparse,hashlib,json
from pathlib import Path
from summarize import stats
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 f=read(E/'matched_freeze.json')
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 correction=read(E/'matched_import_freeze.json')
 for section in ('sources','inputs'):
  for n,h in correction[section].items():assert sha(ROOT/n)==h,n
 cp=read(P/'matched_correction_preregistration.json');assert cp['first_matched_output_absent'] and cp['no_recapture'] and cp['no_math_or_selection_change'] and cp['original_failure_sha256']==sha(P/'matched_sheng.log') and cp['correction_freeze_sha256']==sha(E/'matched_import_freeze.json');assert 'ImportError' in (P/'matched_sheng.log').read_text()
 pre=read(P/'matched_preregistration.json');assert pre['test_capture_absent'] and pre['policy_certificate_absent'] and pre['matched_analysis_absent'] and pre['freeze_sha256']==sha(E/'matched_freeze.json')
 assert (P/'matched_local.json').read_bytes()==(P/'matched_sheng.json').read_bytes()
 m=read(P/'matched_sheng.json');s=read(P/'summary_sheng.json');au=read(P/'audit_test_sheng.json')
 assert m['correction_freeze_sha256']==sha(E/'matched_import_freeze.json') and m['freeze_sha256']==sha(E/'matched_freeze.json') and m['test_audit_sha256']==sha(P/'audit_test_sheng.json') and m['test_outcomes_sha256']==sha(P/'test_capture/outcomes.json')
 assert m['planned_episodes']==72 and m['complete_episodes']==au['captured'] and m['paired_sources']==au['source_scans'] and m['matched_cached_drive_queries']==len(m['cases'])==len(s['cases']) and m['missing_cached_drive_queries']==sum(c['missing_cached_proposal'] for c in s['cells'])
 expected={(c['episode_id'],c['step'],c['cache_step']) for c in s['cases']};actual={(c['episode'],c['step'],c['source_step']) for c in m['cases']};assert expected==actual and len(actual)==len(m['cases'])
 assert m['actual_method_packets_reproduced'] and not m['goal_complete']
 for name in ('function','deadline','cone'):
  assert m['wire_bytes'][name]==sum(c['wire_bytes'][name] for c in m['sources'])
  cell=next(c for c in s['cells'] if c['method']==name);assert cell['actual_wire_bytes_total']==sum(c['wire_bytes'][name] for c in m['sources'] if c['actual_method']==name)
 gaps=[c['function_us']-c['cone_us'] for c in m['cases']];assert gaps==[c['function_minus_cone_us'] for c in m['cases']] and stats(gaps)==m['function_minus_cone_us'] and sum(g==0 for g in gaps)==m['function_cone_identical_age_queries'] and sum(g<0 for g in gaps)==m['cone_age_larger_queries']
 result=dict(matched_sha256=sha(P/'matched_sheng.json'),freeze_sha256=sha(E/'matched_freeze.json'),planned_episodes=72,paired_sources=m['paired_sources'],matched_cached_queries=len(gaps),all_denominators_cross_checked=True,dual_host_bytes_identical=True,actual_physics_rewritten=False,additional_risk_certificate=False,goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
