#!/usr/bin/env python3
"""Lossless per-episode raw observations; run once after all physical work stops."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 assert (P/'terminal.txt').read_text()=='FINITE_USEFUL_EXPIRY_CERTIFICATION_AND_TEST_COMPLETE\n' and read(P/'server_stopped.json')['stopped'];assert (P/'audit_test_sheng.json').exists()
 out=P/'observations';out.mkdir(exist_ok=False);bundles={};seen=set()
 def pack(name,files):
  q=out/(name+'.tar.xz');assert not q.exists();members={}
  with tarfile.open(q,'w:xz',preset=6) as a:
   for f in sorted(files):
    rel=str(f.relative_to(P));assert f.is_file() and not f.is_symlink() and rel not in seen;seen.add(rel);members[rel]=dict(bytes=f.stat().st_size,sha256=sha(f));a.add(f,arcname=rel,recursive=False)
  bundles[str(q.relative_to(P))]=dict(bytes=q.stat().st_size,sha256=sha(q),members=members)
 for split,n in [('certification',540),('test',72)]:
  capture=P/(split+'_capture');outcomes=read(capture/'outcomes.json');assert len(outcomes)==n
  import gzip
  for o in outcomes:
   d=json.loads(gzip.decompress((capture/o['file']).read_bytes()));files=[]
   for s in d['sources']:
    for sub,key,hkey in [('clouds','cloud','cloud_sha256'),('packets','packet','packet_sha256')]:
     f=capture/sub/s[key];assert f.parent==capture/sub and sha(f)==s[hkey];files.append(f)
   pack(o['request']['id'],files)
  allraw=[q for sub in ('clouds','packets') for q in (capture/sub).iterdir() if q.is_file()];residual=[q for q in allraw if str(q.relative_to(P)) not in seen]
  if residual:pack(split+'_preserved_unreferenced',residual)
  assert all(str(q.relative_to(P)) in seen for q in allraw)
 result=dict(bundles=bundles,raw_files=len(seen),raw_bytes=sum(m['bytes'] for b in bundles.values() for m in b['members'].values()),bundle_bytes=sum(b['bytes'] for b in bundles.values()),scope='All original raw scan and wire bytes, including any unreferenced partial files. No content loss or inference changes.')
 (P/'storage_manifest.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bundles'},sort_keys=True))
if __name__=='__main__':main()
