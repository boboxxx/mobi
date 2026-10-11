"""Lossless archives of original files; combined hardlinks are reconstructed."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(exist_ok=False)
root = args.root
files = sorted(p for p in root.rglob('*') if p.is_file())
groups = {f'closed_{i:02d}': [] for i in range(12)}
groups['metadata'] = []
skipped = []
for p in files:
    rel = p.relative_to(root)
    if rel.parts[0] == 'combined' and rel.parts[1] in ('clouds', 'packets', 'episodes') and p.name != 'closed_07.storage_failure.json.gz':
        skipped.append(str(rel))
        continue
    key = 'metadata'
    if rel.parts[0] in ('capture', 'tail_capture') and len(rel.parts) == 3 and rel.parts[1] in ('clouds', 'packets', 'episodes'):
        key = p.name[:9]
        assert key in groups, str(rel)
    groups[key].append(p)
manifest = dict(scope='all original files including incomplete and zero-byte storage failure; combined duplicate hardlinks reconstructed from original frozen records',
    archives={}, files={}, reconstructed_combined_files=skipped)
for key, paths in groups.items():
    archive = args.out/(key+'.tar.xz')
    with tarfile.open(archive, 'w:xz', preset=3) as tar:
        for p in paths:
            rel = str(p.relative_to(root))
            raw = p.read_bytes()
            manifest['files'][rel] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), archive=archive.name)
            tar.add(str(p), arcname=rel, recursive=False)
    raw = archive.read_bytes()
    assert len(raw) < 95*1024*1024, 'GitHub individual-file limit'
    manifest['archives'][archive.name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), files=len(paths))
    print(key, len(paths), len(raw), flush=True)
(args.out/'raw_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
print('PACKAGED', len(manifest['files']), sum(x['bytes'] for x in manifest['archives'].values()), flush=True)
