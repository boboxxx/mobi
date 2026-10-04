#!/usr/bin/env python3
"""Verify every archive member and optionally restore a fresh raw replay tree."""
import argparse,hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--restore',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();m=read(P/'storage_manifest.json');seen=set();total=0
 if a.restore:
  a.restore.mkdir(parents=True,exist_ok=False)
  for split in ('certification_capture','test_capture'):
   src=P/split
   for q in sorted(src.rglob('*')):
    if q.is_file() and q.relative_to(src).parts[0] not in ('clouds','packets'):
     target=a.restore/q.relative_to(P);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,target)
 for name,b in m['bundles'].items():
  q=Path(name);assert not q.is_absolute() and '..' not in q.parts and q.parts[0]=='observations';path=P/q;assert path.stat().st_size==b['bytes'] and sha(path)==b['sha256'];found=set()
  with tarfile.open(path,'r:xz') as tf:
   for item in tf:
    rel=Path(item.name);assert item.isfile() and not rel.is_absolute() and '..' not in rel.parts and len(rel.parts)==3 and rel.parts[0] in ('certification_capture','test_capture') and rel.parts[1] in ('clouds','packets') and item.name in b['members'] and item.name not in seen
    expected=b['members'][item.name];assert item.size==expected['bytes'];h=hashlib.sha256();n=0;dest=None
    if a.restore:
     target=a.restore/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();dest=target.open('wb')
    with tf.extractfile(item) as f:
     for chunk in iter(lambda:f.read(1048576),b''):
      h.update(chunk);n+=len(chunk)
      if dest:dest.write(chunk)
    if dest:dest.close()
    assert n==expected['bytes'] and h.hexdigest()==expected['sha256'];found.add(item.name);seen.add(item.name);total+=n
  assert found==set(b['members'])
 assert len(seen)==m['raw_files'] and total==m['raw_bytes']
 result=dict(storage_manifest_sha256=sha(P/'storage_manifest.json'),raw_files=len(seen),raw_bytes=total,bundles=len(m['bundles']),all_member_bytes_verified=True,scope='Lossless storage verification, not an independent safety certificate.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
