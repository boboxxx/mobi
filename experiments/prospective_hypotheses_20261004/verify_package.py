#!/usr/bin/env python3
"""Verify frozen dependencies, full published outputs, restored logical hashes."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b=f.read(1048576)
            if not b:break
            h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path);a=ap.parse_args()
    for name in ('freeze.json','measurement_freeze.json','minimal_registration_freeze.json'):
        freeze=read(E/name)
        for section in ('sources','inputs'):
            for n,h in freeze[section].items():assert sha(ROOT/n)==h,n
    publication=read(P/'publication_source_manifest.json')
    for section in ('sources','inputs'):
        for n,h in publication[section].items():assert sha(ROOT/n)==h,n
    archive=read(P/'archive.json')
    for name,m in archive['logical_files'].items():assert name in ('qualification_sheng.json','paid_sheng.json','minimal_registration_sheng.json') and sha(P/name)==m['logical_sha256'] and (P/name).stat().st_size==m['logical_bytes']
    manifest=read(P/'artifact_manifest.json');total=0
    for n,m in manifest['files'].items():
        p=ROOT/n;assert n.startswith('results/prospective_hypotheses_20261004/') and not Path(n).is_absolute() and '..' not in Path(n).parts;assert sha(p)==m['sha256'] and p.stat().st_size==m['bytes'],n;total+=m['bytes']
    assert total==manifest['total_bytes'] and len(manifest['files'])==manifest['file_count']
    assert (P/'evaluation_terminal.txt').read_text()=='FINITE_EVALUATION_AND_AUDIT_COMPLETE\n' and read(P/'server_stopped.json')['stopped']
    assert sha(P/'audit_sheng.json')==sha(P/'audit_local.json') and sha(P/'audit_qualification_sheng.json')==sha(P/'audit_qualification_local.json')
    assert sha(P/'audit_minimal_sheng.json')==sha(P/'audit_minimal_local.json') and (P/'minimal_terminal.txt').exists()
    out=dict(artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),files=len(manifest['files']),bytes=total,qualification_sha256=sha(P/'qualification_sheng.json'),paid_sha256=sha(P/'paid_sheng.json'),audit_sha256=sha(P/'audit_sheng.json'),model_and_score_freeze_valid=True,finite_batch_complete=True,goal_complete=False)
    if a.out:a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
