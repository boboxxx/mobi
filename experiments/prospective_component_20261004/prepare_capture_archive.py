#!/usr/bin/env python3
"""Lossless logical JSON archives, never overwrite different data."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
NAMES=('capture/episodes.json',)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--restore',action='store_true');a=ap.parse_args()
    if not a.restore:
        assert not (P/'capture_logical_archives.json').exists();records=[]
        for n in NAMES:
            p=P/n;z=P/(n+'.gz');assert p.exists() and not z.exists()
            with p.open('rb') as source,z.open('wb') as target:
                with gzip.GzipFile(filename='',fileobj=target,mode='wb',mtime=0,compresslevel=6) as out:
                    for b in iter(lambda:source.read(1048576),b''):out.write(b)
            records.append(dict(logical_path=str(p.relative_to(ROOT)),logical_bytes=p.stat().st_size,logical_sha256=sha(p),archive_path=str(z.relative_to(ROOT)),archive_bytes=z.stat().st_size,archive_sha256=sha(z)))
        (P/'capture_logical_archives.json').write_text(json.dumps(dict(records=records,lossless=True),indent=2)+'\n');prior=(P/'.gitignore').read_text() if (P/'.gitignore').exists() else '';assert not any(n in prior.splitlines() for n in NAMES);(P/'.gitignore').write_text(prior+''.join(n+'\n' for n in NAMES))
    m=json.loads((P/'capture_logical_archives.json').read_bytes());assert m['lossless'] and len(m['records'])==len(NAMES)
    for v in m['records']:
        for field in ('logical_path','archive_path'):
            q=Path(v[field]);assert not q.is_absolute() and '..' not in q.parts and q.parts[:2]==('results',E.name)
        p=ROOT/v['logical_path'];z=ROOT/v['archive_path'];assert z.stat().st_size==v['archive_bytes'] and sha(z)==v['archive_sha256'];h=hashlib.sha256();count=0
        if p.exists():assert p.stat().st_size==v['logical_bytes'] and sha(p)==v['logical_sha256']
        with gzip.open(z,'rb') as f:
            if a.restore and not p.exists():
                temp=p.with_suffix(p.suffix+'.restoring');assert not temp.exists()
                with temp.open('xb') as out:
                    for b in iter(lambda:f.read(1048576),b''):out.write(b);h.update(b);count+=len(b)
                assert count==v['logical_bytes'] and h.hexdigest()==v['logical_sha256'];temp.rename(p)
            else:
                for b in iter(lambda:f.read(1048576),b''):h.update(b);count+=len(b)
                assert count==v['logical_bytes'] and h.hexdigest()==v['logical_sha256']
    print('LOSSLESS_ARCHIVES_VERIFIED',len(NAMES),flush=True)
if __name__=='__main__':main()
