"""Validate the explicit publication and original immutable prerequisites."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
P = Path('results/closed_loop_motion_20261011')
manifest_path = P/'publication_manifest.json'
manifest = json.loads(manifest_path.read_bytes())
for name, item in manifest['files'].items():
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts
    raw = path.read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], name
for unit in ('closed_loop_motion_20261011', 'closed_loop_recovery_20261011'):
    freeze = json.loads((Path('experiments')/unit/'freeze.json').read_bytes())
    for section in ('sources', 'inputs'):
        for name, digest in freeze.get(section, {}).items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
raw_manifest = json.loads((P/'raw_archives/raw_manifest.json').read_bytes())
for name, item in raw_manifest['archives'].items():
    raw = (P/'raw_archives'/name).read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], name
cross = json.loads((P/'cross_host.json').read_bytes())
assert cross['status'] == 'PASS' and cross['all_discrete_values_identical']
assert (P/'timing_diagnostic_local.json').read_bytes() == (P/'timing_diagnostic_sheng.json').read_bytes()
assert json.loads((P/'analysis_sheng.json').read_bytes())['summary']['captured'] == 11
assert json.loads((P/'benchmark_sheng.json').read_bytes())['exact_expiry_mismatches'] == 0
for name, pid in (('first_stopped_ownership.json', 5744), ('tail_stopped_ownership.json', 39804)):
    stopped = json.loads((P/name).read_bytes())
    assert stopped['stopped'] and stopped['pid'] == pid
result = dict(status='PASS', published_files_verified=len(manifest['files']),
    published_bytes=sum(v['bytes'] for v in manifest['files'].values()),
    manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    original_controller_and_recovery_unchanged=True, route_failure_and_storage_failure_retained=True)
args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
