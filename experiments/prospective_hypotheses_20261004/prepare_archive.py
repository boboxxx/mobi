#!/usr/bin/env python3
"""Lossless archival of large logical JSON outputs; never edits scientific data."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results'/Path(__file__).resolve().parent.name
FILES=('qualification_sheng.json','paid_sheng.json','minimal_registration_sheng.json')
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--restore',action='store_true');a=ap.parse_args()
    if a.restore:
        info=json.loads((P/'archive.json').read_bytes());assert set(info['logical_files'])==set(FILES)
        for name,m in info['logical_files'].items():
            assert m['archive']==name+'.gz';z=(P/m['archive']).read_bytes();assert len(z)==m['archive_bytes'] and digest(z)==m['archive_sha256'];b=gzip.decompress(z);assert len(b)==m['logical_bytes'] and digest(b)==m['logical_sha256']
            target=P/name
            if target.exists():assert target.read_bytes()==b
            else:target.write_bytes(b)
    else:
        assert (P/'evaluation_terminal.txt').read_text()=='FINITE_EVALUATION_AND_AUDIT_COMPLETE\n' and (P/'minimal_terminal.txt').exists();info=dict(logical_files={},scope='Lossless gzip storage for exact logical qualification/paid/minimal-context JSON; hashes and contents unchanged. Restore before replay.')
        for name in FILES:
            b=(P/name).read_bytes();z=gzip.compress(b,compresslevel=6,mtime=0);assert gzip.decompress(z)==b;(P/(name+'.gz')).write_bytes(z);info['logical_files'][name]=dict(archive=name+'.gz',logical_bytes=len(b),logical_sha256=digest(b),archive_bytes=len(z),archive_sha256=digest(z))
        (P/'archive.json').write_text(json.dumps(info,indent=2,sort_keys=True)+'\n');(P/'.gitignore').write_text(''.join('/'+n+'\n' for n in FILES))
    print('LOSSLESS_HYPOTHESES_ARCHIVE_VALIDATED',flush=True)
if __name__=='__main__':main()
