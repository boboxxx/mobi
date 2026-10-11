"""Validate archives, extract to a new directory, and rebuild combined links."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--archives', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists(), 'Never overwrite a result collection'
manifest = json.loads((args.archives/'raw_manifest.json').read_bytes())
for name, item in manifest['archives'].items():
    raw = (args.archives/name).read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], name
args.out.mkdir(parents=True)
for name in manifest['archives']:
    with tarfile.open(args.archives/name, 'r:xz') as tar:
        for member in tar:
            rel = Path(member.name)
            assert member.isfile() and not rel.is_absolute() and '..' not in rel.parts
            assert member.name in manifest['files'] and manifest['files'][member.name]['archive'] == name
            target = args.out/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            assert not target.exists()
            with tar.extractfile(member) as source, target.open('wb') as destination:
                shutil.copyfileobj(source, destination)
for rel, item in manifest['files'].items():
    raw = (args.out/rel).read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], rel
restored = set()
for part in ('capture', 'tail_capture'):
    base = args.out/part
    for outcome in json.loads((base/'outcomes.json').read_bytes()):
        record = json.loads(gzip.decompress((base/outcome['file']).read_bytes()))
        names = [outcome['file']]+[folder+'/'+s[key] for s in record['sources'] for folder, key in (('clouds', 'cloud'), ('packets', 'packet'))]
        for name in names:
            target = args.out/'combined'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            assert not target.exists()
            try:
                os.link(base/name, target)
            except OSError:
                shutil.copyfile(base/name, target)
            restored.add('combined/'+name)
assert restored == set(manifest['reconstructed_combined_files'])
print(json.dumps(dict(status='PASS', original_files_verified=len(manifest['files']), combined_links_rebuilt=len(restored)), sort_keys=True))
