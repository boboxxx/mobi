#!/usr/bin/env python3
"""Finite development package closure; preserve frozen first audit failure."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert (P/'audit_complete_local.json').read_bytes()==(P/'audit_complete_sheng.json').read_bytes();au=read(P/'audit_complete_sheng.json');assert au['source_sha256']==sha(E/'audit_complete.py') and au['analysis_sha256']==sha(P/'analysis_sheng.json') and au['models_sha256']==sha(P/'models_sheng.json') and not au['fresh_qualification'] and au['rows']==5274 and au['independent_test_age_checks']==12264
    pre=read(P/'preregistration.json');assert pre['published_source_commit']=='b6f8e09b244fb198a4f7ad1947a13212b6cb5c6f' and pre['outputs_absent_before_run'] and pre['already_observed_development_data'] and not pre['goal_complete'] and pre['freeze_sha256']==sha(E/'freeze.json')
    rep=read(P/'audit_repair_receipt.json')
    for field,file in [('original_auditor_sha256',E/'audit.py'),('original_failure_log_sha256',P/'audit_sheng.log'),('completed_auditor_sha256',E/'audit_complete.py'),('model_sha256',P/'models_sheng.json'),('analysis_sha256',P/'analysis_sheng.json'),('radii_sha256',P/'development_radii.json')]:assert rep[field]==sha(file)
    assert rep['model_radii_predictions_unchanged'] and 'AssertionError' in (P/'audit_sheng.log').read_text()
    for host in ('local','sheng'):
        for suf in ('','_before_run'):
            s=(P/('tests_'+host+suf+'.log')).read_text();assert 'Ran 3 tests' in s and s.rstrip().endswith('OK')
    assert (P/'run_terminal.txt').read_text()=='FINITE_STATE_BASELINES_COMPLETE\n' and read(P/'comparison.json')['source_sha256']==sha(E/'compare.py')
    if a.freeze:
        files=sorted(p for p in E.iterdir() if p.is_file())+[ROOT/'research/state_predictor_result_20261004.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files={str(p.relative_to(ROOT)):sha(p) for p in files}))
        write(P/'verification.json',dict(deterministic_audit_pair_sha256=sha(P/'audit_complete_sheng.json'),tests_per_host=3,fresh_qualification=False,paid_policy_evaluated=False,full_goal_complete=False,scope='Frozen finite state prediction baseline development, with all failures and original audit preserved.'))
        files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    for n,h in read(P/'publication_source_manifest.json')['files'].items():assert sha(ROOT/n)==h,n
    m=read(P/'artifact_manifest.json');assert set(m['files'])=={str(p.relative_to(ROOT)) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
    for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
    print(json.dumps(dict(files=m['file_count'],bytes=m['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_audit_pair=True)))
if __name__=='__main__':main()
