#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/nominal_witness_20261003';E=ROOT/'experiments/nominal_witness_20261003'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();pairs=[]
 for stem in ('audit','transfer','summary'):
  local=P/(stem+'_local.json');remote=P/(stem+'_sheng.json');assert local.read_bytes()==remote.read_bytes(),stem;pairs.append(dict(local=local.name,sheng=remote.name,sha256=sha(local)))
 producer=json.loads((P/'search/manifest.json').read_bytes())
 for kind in ('source_hashes','input_hashes'):
  for name,h in producer[kind].items():assert sha(ROOT/name)==h,name
 prior=ROOT/'results/proof_repair_20261003/artifact_manifest.json';assert sha(prior)==producer['prior_artifact_manifest_sha256']
 for name,item in json.loads(prior.read_bytes())['files'].items():assert sha(ROOT/name)==item['sha256'],name
 rows=json.loads((P/'search/rows.json').read_bytes());assert len(rows)==36 and sum(r['evaluations'] for r in rows)==294912
 for r in rows:assert sha(P/'search'/r['search_output'])==r['search_sha256']
 audit=json.loads((P/'audit_sheng.json').read_bytes());assert audit['auditor_sha256']==sha(E/'audit.py') and audit['tasks_with_accepted_pose']==36
 transfer=json.loads((P/'transfer_sheng.json').read_bytes());assert transfer['source_sha256']==sha(E/'transfer.py') and transfer['protocol_sha256']==sha(E/'TRANSFER_PROTOCOL.md') and transfer['initial_audit_sha256']==sha(P/'audit_sheng.json')
 for name,h in transfer['input_hashes'].items():assert sha(ROOT/name)==h,name
 summary=json.loads((P/'summary_sheng.json').read_bytes());assert summary['source_sha256']==sha(E/'summarize.py') and summary['summary']['actual_cannot_cover_fixed_reserve']==7
 for host in ('local','sheng'):
  t=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 3 tests' in t and t.rstrip().endswith('OK')
 if a.freeze:
  sources=set(p for p in E.iterdir() if p.is_file())|{ROOT/n for n in producer['source_hashes']}
  sources.update(ROOT/n for n in ('research/nominal_witness_result_20261003.md','experiments/tube_evidence_20261003/audit.py','experiments/pose_inversion_20261003/audit.py','experiments/terrain_score_20261003/audit.py','experiments/shape_evidence_20261002/audit.py'))
  write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},scope='Frozen study sources and report; rolling root README and project ledger are versioned by the publication commit instead.'))
  write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=3,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Receiver-only upper witnesses and offline fixed-pool raw-data diagnosis; no physical safety, new risk calibration, optimality or online-success claim.'))
  files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and '__pycache__' not in p.parts)
  write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
 sources=json.loads((P/'publication_source_manifest.json').read_bytes())['source_files']
 for name,h in sources.items():assert sha(ROOT/name)==h,name
 artifacts=json.loads((P/'artifact_manifest.json').read_bytes())
 for name,item in artifacts['files'].items():assert sha(ROOT/name)==item['sha256'] and (ROOT/name).stat().st_size==item['bytes'],name
 print(json.dumps(dict(result_files=artifacts['file_count'],source_files=len(sources),artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_pairs=len(pairs))))
if __name__=='__main__':main()
