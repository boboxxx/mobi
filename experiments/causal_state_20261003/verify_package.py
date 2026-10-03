#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'experiments/causal_state_20261003';P=ROOT/'results/causal_state_20261003'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args();pairs=[]
    for stem,script in [('audit','audit.py'),('summary','summarize.py'),('tube_audit','tube_audit.py'),('tube_summary','tube_summary.py'),('support_audit','support_audit.py'),('functional_audit','functional_audit.py'),('functional_summary','functional_summary.py'),('action_functional_audit','action_functional_audit.py'),('action_functional_summary','action_functional_summary.py')]:
        l=P/(stem+'_local.json');r=P/(stem+'_sheng.json');assert l.read_bytes()==r.read_bytes();assert read(r)['source_sha256']==sha(E/script);pairs.append(dict(local=l.name,sheng=r.name,sha256=sha(r)))
    assert read(E/'tube_audit_freeze.json')['source_sha256']==sha(E/'tube_audit.py')
    revision=read(E/'audit_revision.json');assert revision['original_sha256']==sha(E/'audit_at_evaluation.py') and revision['revised_sha256']==sha(E/'audit.py')
    d=read(P/'analysis_sheng.json')
    for mapping in (read(E/'capture_freeze.json')['source_hashes'],read(E/'evaluation_freeze.json')['source_hashes'],d['source_hashes'],d['input_hashes'],read(E/'tube_freeze.json')['source_hashes'],read(P/'tube_sheng.json')['source_hashes'],read(E/'functional_freeze.json')['source_hashes'],read(P/'functional_sheng.json')['source_hashes'],read(E/'action_functional_freeze.json')['source_hashes'],read(P/'action_functional_sheng.json')['source_hashes']):
        for name,h in mapping.items():
            target=E/'audit_at_evaluation.py' if name=='experiments/causal_state_20261003/audit.py' else ROOT/name
            assert sha(target)==h,name
    assert read(E/'evaluation_freeze.json')['prior_freeze_sha256']==sha(E/'evaluation_freeze_before_storage_fix.json')
    assert read(E/'evaluation_freeze.json')['before_empty_shape_fix_sha256']==sha(E/'evaluation_freeze_before_empty_shape_fix.json')
    assert read(E/'evaluation_freeze.json')['before_sampling_timing_sha256']==sha(E/'evaluation_freeze_before_sampling_timing.json')
    assert read(E/'tube_freeze.json')['before_sampling_timing_sha256']==sha(E/'tube_freeze_before_sampling_timing.json')
    assert d['capture_manifest_sha256']==sha(P/'capture/manifest.json')
    assert read(P/'audit_sheng.json')['analysis_sha256']==sha(P/'analysis_sheng.json')
    assert read(P/'support_audit_sheng.json')['analysis_sha256']==sha(P/'analysis_sheng.json')
    for stem in ('tube','functional','action_functional'):
        assert read(P/(stem+'_sheng.json'))['primary_analysis_sha256']==sha(P/'analysis_sheng.json')
        assert read(P/(stem+'_audit_sheng.json'))[stem+'_sha256']==sha(P/(stem+'_sheng.json'))
        assert read(P/(stem+'_audit_sheng.json'))['primary_audit_sha256']==sha(P/'audit_sheng.json')
    capture=read(P/'capture/manifest.json');assert capture['episodes']==len(read(E/'plan.json'))==930
    for r in d['rows']+read(P/'tube_sheng.json')['rows']+read(P/'functional_sheng.json')['rows']+read(P/'action_functional_sheng.json')['rows']:
        for method in ('union','lossless_centers','full_xyz'):
            m=r['methods'][method];assert sha(P/m['packet'])==m['wire_sha256'] and (P/m['packet']).stat().st_size==m['wire_bytes']
            assert all(0<=sample['selection_s']<=sample['source_s'] for sample in m['samples'])
    for host in ('local','sheng'):
        log=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 7 tests' in log and log.rstrip().endswith('OK')
    cleanup=read(P/'capture/cleanup.json');assert all(cleanup[k]==0 for k in ('vehicles','walkers','sensors')) and cleanup['synchronous'] is False
    stopped=read(P/'server_stopped.json');assert stopped['stopped'] is True and stopped['experiment']=='causal_state_20261003'
    extension=read(P/'server_extension.json');assert extension['experiment']==stopped['experiment'] and extension['pid']==stopped['pid'] and extension['finiteGuardMs']==2700000
    if args.freeze:
        sources={p for p in E.iterdir() if p.is_file()}|{ROOT/n for n in d['source_hashes']}|{ROOT/'experiments/positive_state_20261003/audit.py',ROOT/'research/causal_state_result_20261003.md'}
        write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},scope='Study source, report and fixed dependencies; rolling README/project ledger versioned by publication commit.'))
        write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=7,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Finite dynamic frame-local calibration and causal trace execution; no full physical/ego-control/novelty completion.'))
        files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and '__pycache__' not in p.parts)
        write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    source=read(P/'publication_source_manifest.json')
    for name,h in source['source_files'].items():assert sha(ROOT/name)==h,name
    artifacts=read(P/'artifact_manifest.json')
    for name,m in artifacts['files'].items():assert sha(ROOT/name)==m['sha256'] and (ROOT/name).stat().st_size==m['bytes'],name
    print(json.dumps(dict(result_files=artifacts['file_count'],source_files=len(source['source_files']),artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_pairs=len(pairs))))
if __name__=='__main__':main()
