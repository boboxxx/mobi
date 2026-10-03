#!/usr/bin/env python3
"""Verify prospective pre-capture source, complete artifacts and two-host audits."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();d=read(P/'analysis_sheng.json');f=read(P/'action_functional_sheng.json');pairs=[]
    for stem,script in [('audit','audit.py'),('summary','summarize.py'),('action_functional_audit','action_functional_audit.py'),('action_functional_summary','action_functional_summary.py'),('support_audit','support_audit.py'),('tightness','tightness.py')]:
        left=P/(stem+'_local.json');right=P/(stem+'_sheng.json');assert left.read_bytes()==right.read_bytes();assert read(right)['source_sha256']==sha(E/script);pairs.append(dict(stem=stem,sha256=sha(right)))
    for mapping in (read(E/'capture_freeze.json')['source_hashes'],read(E/'action_functional_freeze.json')['source_hashes'],d['source_hashes'],d['input_hashes'],f['source_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    assert read(E/'tightness_freeze.json')['source_sha256']==sha(E/'tightness.py')
    assert d['capture_manifest_sha256']==sha(P/'capture/manifest.json')
    assert read(P/'audit_sheng.json')['analysis_sha256']==sha(P/'analysis_sheng.json')
    assert f['primary_analysis_sha256']==sha(P/'analysis_sheng.json')
    assert read(P/'action_functional_audit_sheng.json')['action_functional_sha256']==sha(P/'action_functional_sheng.json')
    assert read(P/'action_functional_audit_sheng.json')['primary_audit_sha256']==sha(P/'audit_sheng.json')
    assert read(P/'support_audit_sheng.json')['analysis_sha256']==sha(P/'analysis_sheng.json')
    for r in d['rows']+f['rows']:
        for method in ('union','lossless_centers','full_xyz'):
            m=r['methods'][method];assert sha(P/m['packet'])==m['wire_sha256'] and (P/m['packet']).stat().st_size==m['wire_bytes'];assert all(0<=s['selection_s']<=s['source_s'] for s in m['samples'])
    assert read(P/'capture/manifest.json')['episodes']==len(read(E/'plan.json'))==930
    cleanup=read(P/'capture/cleanup.json');assert all(cleanup[k]==0 for k in ('vehicles','walkers','sensors')) and cleanup['synchronous'] is False
    started=read(P/'server_started.json');stopped=read(P/'server_stopped.json');assert started['pid']==stopped['pid'] and stopped['stopped'] is True and stopped['experiment']==E.name
    for host in ('local','sheng'):
        log=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 7 tests' in log and log.rstrip().endswith('OK')
    assert (P/'run_terminal.txt').read_text()=='complete\n'
    if a.freeze:
        sources={p for p in E.iterdir() if p.is_file()}|{ROOT/n for n in d['source_hashes']}|{ROOT/'experiments/positive_state_20261003/audit.py',ROOT/'research/prospective_expiry_result_20261003.md'}
        write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}))
        write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=7,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='One finite prospectively frozen known-class future-snapshot expiry calibration; no arbitrary scene, continuous physical, ego-control or novelty completion.'))
        files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json');write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    for name,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/name)==h,name
    artifact=read(P/'artifact_manifest.json')
    for name,m in artifact['files'].items():assert sha(ROOT/name)==m['sha256'] and (ROOT/name).stat().st_size==m['bytes'],name
    print(json.dumps(dict(result_files=artifact['file_count'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
