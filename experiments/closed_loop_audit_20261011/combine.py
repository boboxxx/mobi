"""Explicit derived collection; failed persistence is never a physical trace."""
import gzip
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT/'results/closed_loop_motion_20261011'
E = ROOT/'experiments/closed_loop_motion_20261011'
plan = json.loads((E/'plan.json').read_bytes())
first = json.loads((P/'capture/outcomes.json').read_bytes())
tail = json.loads((P/'tail_capture/outcomes.json').read_bytes())
assert [x['id'] for x in first] == ['closed_%02d' % i for i in range(7)]
assert [x['id'] for x in tail] == ['closed_%02d' % i for i in range(8, 12)]
assert (P/'capture/episodes/closed_07.json.gz').stat().st_size == 0
OUT = P/'combined'
OUT.mkdir(exist_ok=False)
for name in ('episodes', 'clouds', 'packets'):
    (OUT/name).mkdir()
outcomes = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(source, target, expected):
    assert sha(source) == expected and not target.exists()
    try:
        os.link(str(source), str(target))
    except OSError:
        shutil.copyfile(str(source), str(target))
    assert sha(target) == expected


for request in plan:
    if request['id'] == 'closed_07':
        description = dict(request=request, rows=[], sources=[], collisions=[],
            outcome=dict(status='failed_storage'), synthetic_failure_descriptor=True,
            exception='Original capture exited1: ENOSPC. Attempted closed_07 trace could not be persisted; original zero-byte gzip and partial raw files preserved. Never rerun; no physical values imputed.',
            original_zero_byte_file='capture/episodes/closed_07.json.gz',
            original_terminal_sha256=sha(P/'capture_terminal.txt'))
        logical = (json.dumps(description, sort_keys=True, separators=(',', ':'))+'\n').encode()
        filename = 'episodes/closed_07.storage_failure.json.gz'
        (OUT/filename).write_bytes(gzip.compress(logical, mtime=0))
        outcomes.append(dict(id=request['id'], status='failed_storage', file=filename,
            sha256=sha(OUT/filename), logical_sha256=hashlib.sha256(logical).hexdigest(),
            rows=0, sources=0, synthetic_failure_descriptor=True))
        continue
    base, original = next((P/part, item) for part, values in (('capture', first), ('tail_capture', tail)) for item in values if item['id'] == request['id'])
    record = json.loads(gzip.decompress((base/original['file']).read_bytes()))
    assert record['request'] == request and original['status'] == 'captured'
    link(base/original['file'], OUT/original['file'], original['sha256'])
    for source in record['sources']:
        for folder, key in (('clouds', 'cloud'), ('packets', 'packet')):
            link(base/folder/source[key], OUT/folder/source[key], source[key+'_sha256'])
    outcomes.append(original)
(OUT/'outcomes.json').write_text(json.dumps(outcomes, indent=2, sort_keys=True)+'\n')
(OUT/'plan.json').write_bytes((E/'plan.json').read_bytes())
(OUT/'context.json').write_bytes((P/'capture/context.json').read_bytes())
assert (P/'capture/context.json').read_bytes() == (P/'tail_capture/context.json').read_bytes()
receipt = dict(original_planned=12, physically_recorded_complete=11, attempted_storage_failure='closed_07',
    synthetic_failure_descriptor_is_not_a_trajectory=True, original_run_exit_code=1,
    no_attempted_request_rerun=True, preserved_original_outcomes_sha256=sha(P/'capture/outcomes.json'),
    preserved_tail_outcomes_sha256=sha(P/'tail_capture/outcomes.json'), freeze_sha256=sha(E/'freeze.json'))
(OUT/'collection_receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
print(json.dumps(receipt, sort_keys=True))
