#!/usr/bin/env python3
"""Freeze explicitly, otherwise verify an existing immutable publication package."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'results/proof_repair_20261003'
E=ROOT/'experiments/proof_repair_20261003'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj): p.write_text(json.dumps(obj,indent=2)+'\n')

def check():
    pairs=[]
    for local,remote in [('audit_local.json','audit_sheng.json'),
                         ('audit_adaptive_local.json','audit_adaptive_sheng.json'),
                         ('summary_local.json','summary_sheng.json')]:
        assert (P/local).read_bytes()==(P/remote).read_bytes(),(local,remote)
        pairs.append(dict(local=local,sheng=remote,sha256=sha(P/local)))
    deps=set()
    for study,auditor in [('replay','audit.py'),('adaptive','audit_adaptive.py')]:
        producer=json.loads((P/study/'manifest.json').read_bytes())
        assert producer['rows']==108
        for name,digest in producer['source_hashes'].items():
            assert sha(ROOT/name)==digest,name
            deps.add(ROOT/name)
        prior=ROOT/'results/tube_evidence_20261003/artifact_manifest.json'
        assert sha(prior)==producer['prior_artifact_manifest_sha256']
        for name,record in json.loads(prior.read_bytes())['files'].items():
            assert sha(ROOT/name)==record['sha256'],name
        audit=P/('audit_sheng.json' if study=='replay' else 'audit_adaptive_sheng.json')
        result=json.loads(audit.read_bytes())
        assert result['audit_sha256']==sha(E/auditor)
        assert len(result['rows'])==108 and result['upper_witnesses']==0
        for row in json.loads((P/study/'rows.json').read_bytes()):
            assert sha(P/study/row['repair_output'])==row['repair_sha256']
    for host in ('local','sheng'):
        test=(P/('tests_'+host+'.txt')).read_text()
        assert 'Ran 6 tests' in test and test.rstrip().endswith('OK')
    summary=json.loads((P/'summary_sheng.json').read_bytes())
    assert summary['source_sha256']==sha(E/'summarize.py')
    assert len(summary['fixed_rows'])==108 and len(summary['adaptive_tasks'])==36
    assert summary['max_initialization_wait_us']==0
    assert summary['fixed_direct_baseline']['positive_remaining']==7
    assert summary['adaptive_summary']['all_three_positive_tasks']==7
    assert summary['adaptive_summary']['direct_all_three_positive_tasks']==6
    return pairs,deps

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--freeze',action='store_true')
    a=ap.parse_args()
    pairs,deps=check()
    if a.freeze:
        files=set(p for p in E.iterdir() if p.is_file())|deps
        files.update(ROOT/p for p in ('README.md','research/PROJECT_STATUS.md',
            'research/proof_repair_result_20261003.md',
            'experiments/tube_evidence_20261003/audit.py',
            'experiments/expiry_runtime_20261003/reference.cpp',
            'experiments/pose_inversion_20261003/audit.py',
            'experiments/terrain_score_20261003/audit.py',
            'experiments/shape_evidence_20261002/audit.py'))
        write(P/'publication_source_manifest.json',dict(
            base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}))
        write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=6,
            source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,
            scope='Finite saved-message proof repair and causal stopping; posthoc adaptive development. Same saved sheng outputs audited independently on two hosts. No full scene coverage, near-optimality, deployment-risk or physical-control claim.'))
        files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and '__pycache__' not in p.parts)
        write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    sources=json.loads((P/'publication_source_manifest.json').read_bytes())
    for name,digest in sources['source_files'].items(): assert sha(ROOT/name)==digest,name
    artifacts=json.loads((P/'artifact_manifest.json').read_bytes())
    for name,record in artifacts['files'].items():
        p=ROOT/name
        assert sha(p)==record['sha256'] and p.stat().st_size==record['bytes'],name
    print(json.dumps(dict(result_files=artifacts['file_count'],source_files=len(sources['source_files']),
        artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_pairs=len(pairs))))

if __name__=='__main__':main()
