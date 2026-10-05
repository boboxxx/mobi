#!/usr/bin/env python3
"""Restore missing frozen logical inputs from committed gzip; never replace input."""
import argparse,gzip,hashlib,json,os,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();f=json.loads((E/'freeze.json').read_text());verified={};restored=0
 for name,digest in f['inputs'].items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] in ('results','experiments');p=R/rel
  if not p.exists():
   assert rel.parts[0]=='results'
   source=p.with_name(p.name+'.gz');assert source.is_file(),str(source)
   fd,temporary=tempfile.mkstemp(prefix=p.name+'.restore-',dir=p.parent);tmp=Path(temporary)
   try:
    with os.fdopen(fd,'wb') as dst,gzip.open(source,'rb') as src:
     for chunk in iter(lambda:src.read(1048576),b''):dst.write(chunk)
    assert sha(tmp)==digest,name
    # Link only if destination remains absent; atomic and never overwrites.
    os.link(str(tmp),str(p));restored+=1
   finally:
    if tmp.exists():tmp.unlink()
  assert p.is_file() and not p.is_symlink() and sha(p)==digest,name
  verified[name]=dict(sha256=digest,bytes=p.stat().st_size)
 result=dict(freeze_sha256=sha(E/'freeze.json'),verified_inputs=verified,all_input_bytes_verified=True,scope='Exact logical restoration only; no fitting, remeasurement or replacement of existing inputs.')
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('INPUTS_VERIFIED',len(verified),'MISSING_LOGICAL_FILES_RESTORED',restored)
if __name__=='__main__':main()
