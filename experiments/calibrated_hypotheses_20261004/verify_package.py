#!/usr/bin/env python3
"""Close finite development outputs while retaining frozen sources and scope."""
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
    assert (P/'audit_local.json').read_bytes()==(P/'audit_sheng.json').read_bytes();au=read(P/'audit_sheng.json');assert au['rows']==5274 and au['independent_geometry_checks']==12276 and au['source_sha256']==sha(E/'audit_development.py') and au['development_sha256']==sha(P/'development_sheng.json') and au['models_sha256']==sha(P/'models_sheng.json') and not au['fresh_qualification']
    pre=read(P/'preregistration.json');assert pre['published_source_commit']=='ecc41ef9ae66a68005852d9208f3fd19a4dab90c' and pre['outputs_absent_before_run'] and pre['development_data_previously_observed'] and not pre['goal_complete'] and pre['freeze_sha256']==sha(E/'freeze.json')
    for host in ('local','sheng'):
        for suf in ('','_before_run'):
            s=(P/('tests_'+host+suf+'.log')).read_text();assert 'Ran 4 tests' in s and s.rstrip().endswith('OK')
    assert (P/'run_terminal.txt').read_text()=='FINITE_HYPOTHESES_DEVELOPMENT_COMPLETE\n'
    if a.freeze:
        files=sorted(p for p in E.iterdir() if p.is_file())+[ROOT/'research/calibrated_hypotheses_result_20261004.md'];write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files={str(p.relative_to(ROOT)):sha(p) for p in files}))
        write(P/'verification.json',dict(deterministic_audit_pair_sha256=sha(P/'audit_sheng.json'),tests_per_host=4,fresh_qualification=False,paid_policy_evaluated=False,full_goal_complete=False,scope='Frozen finite support guard/local-scale/geometry-pruning development, not independent qualification or novelty.'))
        files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    for n,h in read(P/'publication_source_manifest.json')['files'].items():assert sha(ROOT/n)==h,n
    m=read(P/'artifact_manifest.json');assert set(m['files'])=={str(p.relative_to(ROOT)) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}
    for n,v in m['files'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'],n
    print(json.dumps(dict(files=m['file_count'],bytes=m['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_audit_pair=True)))
if __name__=='__main__':main()
