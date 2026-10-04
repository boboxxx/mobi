#!/usr/bin/env python3
"""Freeze all three fixed policies only after safety AND usefulness tests."""
import hashlib,importlib.util,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
s=importlib.util.spec_from_file_location('useful_fixed_binomial',ROOT/'experiments/balanced_expiry_20261004/conditional.py');risk=importlib.util.module_from_spec(s);s.loader.exec_module(risk)
s=importlib.util.spec_from_file_location('useful_fixed_utility',E/'utility.py');U=importlib.util.module_from_spec(s);s.loader.exec_module(U)
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (P/'policy_frozen.json').exists() and not (P/'test_capture').exists()
 f=read(E/'freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 a=read(P/'audit_certification_sheng.json');plan=[v for v in read(E/'plan.json') if v['split']=='certification'];labels=a['risk_labels'];assert len(labels)==len(plan)==540 and [v['id'] for v in labels]==[v['id'] for v in plan] and a['freeze_sha256']==sha(E/'freeze.json') and a['outcomes_sha256']==sha(P/'certification_capture/outcomes.json')
 methods={}
 for method in ('function','deadline','cone'):
  rows=[v for v in labels if v['method']==method];assert len(rows)==180
  c=risk.certificate([v['selected'] for v in rows],[v['failed'] for v in rows],risk=F(1,20),delta=F(1,20),policies=6)
  c['risk_accepted']=c['accepted'];c['utility']=U.certificate([v['useful'] for v in rows]);c['accepted']=c['risk_accepted'] and c['utility']['accepted'];c['scope']='Fixed3s/30-source immediate receiver law under joint IID scene/service/execution. Conditional risk AND unconditional useful-progress lower bound, not road/radio/continuous or unknown-actor certification.';methods[method]=c
 required=risk.zero_failure_required(F(1,20),F(1,20),6);assert required==94
 result=dict(methods=methods,certification_complete=True,test_capture_absent_when_frozen=True,binary_tests=6,zero_failure_accepted_required=required,risk_target=[1,20],utility_target=[1,4],progress_threshold_um=50000,joint_confidence_error_budget=[1,20],freeze_sha256=sha(E/'freeze.json'),audit_sha256=sha(P/'audit_certification_sheng.json'),scene_law=read(E/'SCENE_LAW.json'),source_observations_per_episode=30,drive_steps=60,control_step_us=50000,action_us=300000,decision_budget_us=20000,source_period_steps=2,production_road_authorized=False,goal_complete=False)
 (P/'policy_frozen.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(dict(accepted_methods=sum(v['accepted'] for v in methods.values()),methods={k:{n:v[n] for n in ('authorized_episodes','failed_authorized_episodes','conditional_upper','risk_accepted','utility','accepted')} for k,v in methods.items()}),sort_keys=True))
if __name__=='__main__':main()
