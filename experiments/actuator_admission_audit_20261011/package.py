"""Every raw file, grouped by declared episode for GitHub file-size limits."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
args.out.mkdir(exist_ok=False)
outcomes=json.loads((args.root/'capture/outcomes.json').read_bytes())
groups={o['id']:[] for o in outcomes};groups['metadata']=[]
for path in sorted(args.root.rglob('*')):
 if not path.is_file():continue
 key='metadata';rel=path.relative_to(args.root)
 if len(rel.parts)==3 and rel.parts[0]=='capture' and rel.parts[1] in ('clouds','packets','episodes'):
  key=next(k for k in groups if k!='metadata' and path.name.startswith(k+('_' if rel.parts[1]!='episodes' else '.')))
 groups[key].append(path)
manifest=dict(scope='all raw files including failed outcomes; no imputation',archives={},files={})
for key,paths in groups.items():
 archive=args.out/(key+'.tar.xz')
 with tarfile.open(archive,'w:xz',preset=3) as tar:
  for path in paths:
   rel=str(path.relative_to(args.root));raw=path.read_bytes();manifest['files'][rel]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),archive=archive.name);tar.add(path,arcname=rel,recursive=False)
 raw=archive.read_bytes();assert len(raw)<95*1024**2
 manifest['archives'][archive.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),files=len(paths))
 print(key,len(paths),len(raw),flush=True)
(args.out/'raw_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('LOSSLESS_PACKAGE_COMPLETE',len(manifest['files']),sum(v['bytes'] for v in manifest['archives'].values()),flush=True)
