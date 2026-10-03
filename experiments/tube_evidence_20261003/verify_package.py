#!/usr/bin/env python3
"""Verify deterministic host pairs and freeze the finite publication package."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/tube_evidence_20261003';E=ROOT/'experiments/tube_evidence_20261003'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def main():
 pairs=[]
 for local,remote in [('audit_local.json','audit_sheng.json'),('witnesses_local.json','witnesses_sheng.json'),('summary_local.json','summary_sheng.json')]:
  assert (P/local).read_bytes()==(P/remote).read_bytes(),(local,remote);pairs.append(dict(local=local,sheng=remote,sha256=sha(P/local)))
 producer=json.loads((P/'replay/manifest.json').read_bytes())
 for name,digest in producer['source_hashes'].items():assert sha(ROOT/name)==digest,name
 audit=json.loads((P/'audit_sheng.json').read_bytes());assert audit['message_coverage_checks']==108 and len(audit['fingerprints'])==36 and len(audit['same_partition_tightness'])==108
 assert audit['audit_sha256']==sha(E/'audit.py')
 for host in ('local','sheng'):
  test=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 5 tests' in test and test.rstrip().endswith('OK')
 summary=json.loads((P/'summary_sheng.json').read_bytes());assert len(summary['rows'])==108 and len(summary['groups'])==9;assert summary['source_sha256']==sha(E/'summarize.py')
 assert all(r['initialization_wait_us']==0 for r in summary['rows'])
 files=[p for p in E.iterdir() if p.is_file()]+[ROOT/p for p in ('README.md','research/PROJECT_STATUS.md','research/tube_evidence_result_20261003.md','research/tube_evidence_reading_20261003.md')]+[ROOT/p for p in producer['source_hashes']]+[ROOT/'experiments/expiry_runtime_20261003/reference.cpp',ROOT/'experiments/pose_inversion_20261003/audit.py',ROOT/'experiments/terrain_score_20261003/audit.py',ROOT/'experiments/shape_evidence_20261002/audit.py'];files=sorted(set(files))
 write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in files}))
 write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=5,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Pointwise bounded-current-evidence replay; same inherited revalidation rule only for representation-loss diagnostic; no complete physical scene coverage, optimality or deployment-risk claim.'))
 results=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and '__pycache__' not in p.parts)
 write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in results},file_count=len(results),total_bytes=sum(p.stat().st_size for p in results)))
 print(json.dumps(dict(result_files=len(results),source_files=len(files),artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_pairs=len(pairs))))
if __name__=='__main__':main()
