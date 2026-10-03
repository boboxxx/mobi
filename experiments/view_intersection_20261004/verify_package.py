#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args()
    d=read(P/'analysis_sheng.json');pairs=[]
    parent=read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json')
    for name,script in [('audit','audit.py'),('summary','summarize.py'),('ambiguity','ambiguity.py')]:
        assert (P/(name+'_local.json')).read_bytes()==(P/(name+'_sheng.json')).read_bytes()
        out=read(P/(name+'_sheng.json'));assert out['source_sha256']==sha(E/script) and out['analysis_sha256']==sha(P/'analysis_sheng.json')
        pairs.append(dict(stem=name,sha256=sha(P/(name+'_sheng.json'))))
    for mapping in (d['source_hashes'],d['input_hashes'],read(E/'freeze.json')['source_hashes'],read(E/'freeze.json')['input_hashes'],parent['source_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    archived={'kernel.py':'kernel_at_first_run.py','test_kernel.py':'kernel_tests_at_first_run.py'}
    for name,h in read(E/'freeze_at_first_run.json')['source_hashes'].items():
        target=ROOT/name
        if target.parent==E and target.name in archived:target=E/archived[target.name]
        assert sha(target)==h,name
    old=(E/'kernel_at_first_run.py').read_text();new=(E/'kernel.py').read_text()
    assert new.replace('if d2 == 0 or sum((p[k]-other[k])**2 for k in range(2)) <= rr*rr:','if sum((p[k]-other[k])**2 for k in range(2)) <= rr*rr:')==old
    revision=read(E/'numerical_revision.json');assert revision['original_kernel_sha256']==sha(E/'kernel_at_first_run.py') and revision['repaired_kernel_sha256']==sha(E/'kernel.py') and revision['policy_data_risk_parameters_changed'] is False
    assert 'AssertionError' in (P/'evaluate_sheng_initial_failure.log').read_text()
    assert read(P/'summary_sheng.json')['audit_sha256']==sha(P/'audit_sheng.json')
    assert read(P/'ambiguity_sheng.json')['audit_sha256']==sha(P/'audit_sheng.json') and read(P/'ambiguity_sheng.json')['certificate_auditor_sha256']==sha(E/'audit.py')
    assert len(d['traces'])==2160 and len(d['rows'])==2076 and len(d['pairs'])==1038
    for host in ('local','sheng'):
        log=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 13 tests' in log and log.rstrip().endswith('OK')
    assert (P/'run_terminal.txt').read_text()=='complete\n'
    if a.freeze:
        sources={p for p in E.iterdir() if p.is_file()}|{ROOT/'research/view_intersection_result_20261004.md'}|{ROOT/name for name in parent['source_hashes']}
        write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}))
        write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=13,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Finite receiver intersection development; inherited state risk event and explicit motion/body assumptions. Model distance/expiry bracket, not raw/physical conservatism or novelty completion.'))
        files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json')
        write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    for name,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/name)==h,name
    artifact=read(P/'artifact_manifest.json')
    assert {str(p.relative_to(ROOT)) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}==set(artifact['files'])
    for name,m in artifact['files'].items():assert sha(ROOT/name)==m['sha256'] and (ROOT/name).stat().st_size==m['bytes'],name
    print(json.dumps(dict(result_files=artifact['file_count'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
