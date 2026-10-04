#!/usr/bin/env python3
"""Pre-fixed whole-episode selective test; no inherited six-frame certificate."""
import argparse,hashlib,importlib.util,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
spec=importlib.util.spec_from_file_location('episode_fixed_exact_binomial',ROOT/'experiments/balanced_expiry_20261004/conditional.py');stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 assert not (P/'policy_frozen.json').exists() and not (P/'test_capture').exists()
 f=read(E/'freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 audit=read(P/'audit_certification_sheng.json');plan=[v for v in read(E/'plan.json') if v['split']=='certification'];labels=audit['risk_labels'];assert len(plan)==len(labels)==540 and [v['id'] for v in labels]==[v['id'] for v in plan];assert audit['split']=='certification' and audit['freeze_sha256']==sha(E/'freeze.json') and audit['outcomes_sha256']==sha(P/'certification_capture/outcomes.json')
 cells={}
 for method in ('function','deadline','cone'):
  rows=[v for v in labels if v['method']==method];assert len(rows)==180
  c=stats.certificate([v['selected'] for v in rows],[v['failed'] for v in rows],risk=F(1,20),delta=F(1,20),policies=3)
  c['scope']='Conditional on at least one experimental geometry authorization in the fixed3s/20-source ego episode, under the declared joint IID scene+measured service law. Failure is any used-source center exclusion, source-action age violation, recorded sampled operational violation/collision, or incomplete accepted capture. Not continuous-road, unknown-actor, per-query or actual-radio risk.'
  cells[method]=c
 result=dict(methods=cells,certification_complete=True,test_capture_absent_when_frozen=True,risk_target=[1,20],joint_confidence_error_budget=[1,20],binary_tests=3,zero_failure_accepted_required=stats.zero_failure_required(F(1,20),F(1,20),3),freeze_sha256=sha(E/'freeze.json'),audit_sha256=sha(P/'audit_certification_sheng.json'),scene_law=read(E/'SCENE_LAW.json'),source_observations_per_episode=20,drive_steps=60,control_step_us=50000,action_us=300000,source_period_steps=3,production_road_authorized=False,goal_complete=False)
 (P/'policy_frozen.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(accepted_methods=sum(v['accepted'] for v in cells.values()),methods=cells,zero_failure_accepted_required=result['zero_failure_accepted_required']),sort_keys=True))
if __name__=='__main__':main()
