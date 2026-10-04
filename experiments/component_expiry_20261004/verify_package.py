#!/usr/bin/env python3
"""Prepare/verify complete source and artifact closure for this finite probe."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path);a=ap.parse_args();f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert (P/'terminal.txt').read_text()=='FINITE_COMPONENT_DEVELOPMENT_AND_AUDIT_COMPLETE\n'
    assert (P/'audit_local.json').read_bytes()==(P/'audit_sheng.json').read_bytes()
    assert not read(P/'development_sheng.json')['fresh_qualification']
    if a.prepare:
        sources=dict(f['sources']);inputs=dict(f['inputs'])
        for p in E.iterdir():
            if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
        n='research/balanced_expiry_result_20261004.md';sources[n]=sha(ROOT/n)
        write(P/'publication_source_manifest.json',dict(sources=sources,inputs=inputs,fresh_qualification=False))
        files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name not in EXCLUDE}
        write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),noncircular_exclusions=sorted(EXCLUDE),fresh_qualification=False))
    pub=read(P/'publication_source_manifest.json')
    for section in ('sources','inputs'):
        for n,h in pub[section].items():assert sha(ROOT/n)==h,n
    m=read(P/'artifact_manifest.json');actual={str(p.relative_to(ROOT)) for p in P.rglob('*') if p.is_file() and p.name not in EXCLUDE};assert actual==set(m['files'])
    for n,v in m['files'].items():assert not Path(n).is_absolute() and '..' not in Path(n).parts and n.startswith('results/component_expiry_20261004/') and sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes']
    assert m['total_bytes']==sum(v['bytes'] for v in m['files'].values()) and m['file_count']==len(m['files'])
    out=dict(artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),files=m['file_count'],bytes=m['total_bytes'],development_sha256=sha(P/'development_sheng.json'),audit_sha256=sha(P/'audit_sheng.json'),frozen_code_valid=True,finite_probe_complete=True,fresh_qualification=False,goal_complete=False)
    if a.out:write(a.out,out)
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
