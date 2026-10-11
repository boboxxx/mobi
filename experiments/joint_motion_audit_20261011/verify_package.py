"""Verify the explicitly published files and the immutable source freeze."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
P = Path('results/joint_motion_expiry_20261011')
manifest_path = P/'publication_manifest.json'
manifest = json.loads(manifest_path.read_bytes())
for name, item in manifest['files'].items():
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts
    data = path.read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], name
freeze = json.loads(Path('experiments/joint_motion_expiry_20261011/freeze.json').read_bytes())
for section in ('sources', 'inputs'):
    for name, digest in freeze[section].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert manifest['archive_sha256'] == hashlib.sha256((P/'sheng_full_data.tar.xz').read_bytes()).hexdigest()
assert json.loads((P/'audit_sheng.json').read_bytes())['status'] == 'PASS'
assert (P/'audit_sheng.json').read_bytes() == (P/'audit_local.json').read_bytes()
assert json.loads((P/'cross_host.json').read_bytes())['all_decisions_packets_prefixes_fees_bounds_counts_identical']
assert json.loads((P/'stopped_ownership.json').read_bytes())['stopped']
receipt = dict(status='PASS', published_files_verified=len(manifest['files']),
    published_bytes=sum(v['bytes'] for v in manifest['files'].values()),
    publication_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    frozen_sources_unchanged=True, archive_and_scientific_audits_verified=True)
args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
print(json.dumps(receipt, sort_keys=True))
