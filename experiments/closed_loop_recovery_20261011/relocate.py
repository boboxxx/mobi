"""Byte-preserving relocation of this task's results only; no other cleanup."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('/home/sheng/mobicom2027_visibility_20261001')
SOURCE = ROOT/'results/closed_loop_motion_20261011'
DEST = Path('/mnt/c/Users/Administrator/mobi-closed-loop-motion-data-20261011')
FREEZE = '8254fe6c30a1f7dacbfb78191659efeea1158a987eea1fec3cdd1ccacb67354e'
assert hashlib.sha256((ROOT/'experiments/closed_loop_motion_20261011/freeze.json').read_bytes()).hexdigest() == FREEZE
assert SOURCE.exists() and not SOURCE.is_symlink()
files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
assert files and not any(p.is_symlink() for p in SOURCE.rglob('*'))
DEST.mkdir(exist_ok=True)
manifest = {}
for path in files:
    name = path.relative_to(SOURCE)
    target = DEST/name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.stat().st_size == path.stat().st_size and hashlib.sha256(target.read_bytes()).hexdigest() == digest, str(target)
    else:
        shutil.copy2(str(path), str(target))
    assert target.stat().st_size == path.stat().st_size and hashlib.sha256(target.read_bytes()).hexdigest() == digest
    manifest[str(name)] = dict(bytes=path.stat().st_size, sha256=digest)
receipt = dict(status='ALL_COPIES_BYTE_VERIFIED_BEFORE_SOURCE_REMOVAL', source=str(SOURCE), destination=str(DEST),
               files=manifest, bytes=sum(item['bytes'] for item in manifest.values()), freeze_sha256=FREEZE,
               operation='Relocate only owned result directory; replace old path with symlink; preserve partial files.')
(DEST/'relocation_receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
# Only verified task-owned duplicates are removed; the original bytes remain.
for path in files:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest[str(path.relative_to(SOURCE))]['sha256']
    path.unlink()
for directory in sorted((p for p in SOURCE.rglob('*') if p.is_dir()), key=lambda p:len(p.parts), reverse=True):
    directory.rmdir()
SOURCE.rmdir()
SOURCE.symlink_to(DEST, target_is_directory=True)
for name, item in manifest.items():
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() == item['sha256']
print(json.dumps({'status':'RELOCATED_AND_SYMLINK_VERIFIED','files':len(files),'bytes':receipt['bytes'],'source':str(SOURCE),'destination':str(DEST)}))
