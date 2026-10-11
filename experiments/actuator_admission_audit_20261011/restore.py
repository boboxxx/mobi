"""Verify and restore to a fresh folder; no existing files overwritten."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser=argparse.ArgumentParser();parser.add_argument('--archives',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
assert not args.out.exists();manifest=json.loads((args.archives/'raw_manifest.json').read_bytes())
for name,item in manifest['archives'].items():
 raw=(args.archives/name).read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],name
args.out.mkdir(parents=True)
seen=set()
for name in manifest['archives']:
 with tarfile.open(args.archives/name,'r:xz') as tar:
  for m in tar:
   p=Path(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name not in seen
   item=manifest['files'][m.name];assert item['archive']==name
   raw=tar.extractfile(m).read();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],m.name
   dest=args.out/p;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();dest.write_bytes(raw);seen.add(m.name)
assert seen==set(manifest['files']);print('RAW_FILES_VERIFIED',len(seen))
