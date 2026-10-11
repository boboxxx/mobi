"""Restore the published lossless sheng package without replacing any file."""
import hashlib
import json
import tarfile
from pathlib import Path

ARCHIVE = Path('results/joint_motion_expiry_20261011/sheng_full_data.tar.xz')
EXPECTED = 'ab011ff6238644f8f28396e5d5d7f6192f59ff84cfc76d95c9e72ce4d8cb660a'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == EXPECTED
with tarfile.open(ARCHIVE, 'r:xz') as tar:
    members = tar.getmembers()
    manifest_member = next(m for m in members if m.name == 'results/joint_motion_expiry_20261011/export_manifest.json')
    manifest = json.loads(tar.extractfile(manifest_member).read())
    assert len(members) == manifest['file_count']+1
    restored = 0
    for member in members:
        path = Path(member.name)
        assert member.isfile() and not path.is_absolute() and '..' not in path.parts
        assert path.parts[:2] == ('results', 'joint_motion_expiry_20261011')
        data = tar.extractfile(member).read()
        if member is not manifest_member:
            check = manifest['files'][member.name]
            assert len(data) == check['bytes'] and hashlib.sha256(data).hexdigest() == check['sha256']
        if path.exists():
            assert path.read_bytes() == data, 'Refusing to replace: '+str(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            restored += 1
print(json.dumps({'archive_verified': True, 'files_verified': len(members), 'new_files_restored': restored}))
