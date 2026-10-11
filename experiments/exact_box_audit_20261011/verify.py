"""Explicit publication hashes and exact scientific equality across hosts."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
P=Path('results/exact_box_expiry_20261011')
manifest=json.loads((P/'publication_manifest.json').read_bytes())
for name,item in manifest['files'].items():
    raw=Path(name).read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'], name
freeze=json.loads(Path('experiments/exact_box_expiry_20261011/freeze.json').read_bytes())
for section in ('sources','inputs'):
    for name,digest in freeze[section].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest, name
a=json.loads((P/'replay_sheng.json').read_bytes())
b=json.loads((P/'replay_local.json').read_bytes())
omit={'original_fast_fee_us','additional_exact_fee_us','replay_total_with_original_receiver_and_rpc_us','new_shadow_with_measured_replay_budget'}
assert a['freeze_sha256']==b['freeze_sha256'] and a['scope']==b['scope']
assert len(a['rows'])==len(b['rows'])==6905
for x,y in zip(a['rows'],b['rows']):
    assert {k:v for k,v in x.items() if k not in omit}=={k:v for k,v in y.items() if k not in omit}
    assert x['original_prefix_us']<=x['combined_prefix_us']<=500000
for key in ('queries','exact_box_evaluated','improved_prefixes','maximum_prefix_gain_us','original_shadow_allowed','new_shadow_allowed','shadow_gains','shadow_losses'):
    assert a['summary'][key]==b['summary'][key], key
assert a['summary']['shadow_gains']==a['summary']['shadow_losses']==0
result=dict(status='PASS',published_files_verified=len(manifest['files']),
    published_bytes=sum(x['bytes'] for x in manifest['files'].values()),
    manifest_sha256=hashlib.sha256((P/'publication_manifest.json').read_bytes()).hexdigest(),
    scientific_queries_identical=6905,measured_fees_and_fee_budget_filter_not_required_identical=True,
    source_freeze_unchanged=True,shadow_counts_are_not_new_physical_rollouts=True)
args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
