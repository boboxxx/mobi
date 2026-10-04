#!/usr/bin/env python3
"""Post-result byte closure and finite-scope verification; never recalibrate."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = Path(__file__).resolve().parent
P = ROOT/'results'/E.name
EXCLUDE = {'artifact_manifest.json', 'verification_local.json', 'verification_sheng.json'}
REPORT = 'research/action_expiry_interface_result_20261004.md'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_bytes())


def write(p, d):
    assert not p.exists(), p
    p.write_text(json.dumps(d, indent=2, sort_keys=True)+'\n')


def artifacts():
    return {str(p.relative_to(ROOT)): p for p in sorted(P.iterdir())
            if p.is_file() and p.name not in EXCLUDE}


def verify_hashes(section):
    for n, h in section.items():
        q = Path(n)
        assert not q.is_absolute() and '..' not in q.parts
        assert sha(ROOT/n) == h, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepare', action='store_true')
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    frozen = read(E/'freeze.json')
    for section in ('sources', 'inputs'):
        verify_hashes(frozen[section])
    assert (P/'terminal.txt').read_text() == 'FINITE_ACTION_QUERY_REPLAY_AND_AUDIT_COMPLETE\n'
    assert (P/'audit_local.json').read_bytes() == (P/'audit_sheng.json').read_bytes()
    probe, audit, pre = [read(P/n) for n in ('probe_sheng.json', 'audit_sheng.json', 'preregistration.json')]
    assert pre['cases_absent_before_run'] and not pre['new_capture_or_risk_qualification']
    assert pre['freeze_sha256'] == sha(E/'freeze.json')
    assert pre['sources'] == len(frozen['sources']) == 107
    assert pre['inputs'] == len(frozen['inputs']) == 33
    assert not probe['goal_complete'] and not audit['goal_complete']
    stats, by_radius, counts = Counter(), {}, Counter()
    for line in (P/'cases_sheng.jsonl').open():
        case = json.loads(line)
        prop, gate = case['proposal'], case['gate']
        assert not prop['deployment_authorized'] and not prop['risk_certificate_applicable'] and not gate['deployment_authorized']
        stats['queries'] += 1
        stats['geometry_eligible'] += gate['geometry_eligible']
        counts[prop['status']] += 1
        old = case['historical_lower_us']
        if old is not None:
            stats['fixed_equal' if prop['lower_us'] == old else 'fixed_increased' if prop['lower_us'] > old else 'fixed_decreased'] += 1
        key = case['family']+':'+str(prop['query_radius_um'])
        row = by_radius.setdefault(key, Counter())
        row['queries'] += 1
        row['positive'] += prop['lower_us'] > 0
        row['geometry_eligible'] += gate['geometry_eligible']
    assert stats['queries'] == audit['queries'] == probe['stats']['queries'] == 65472
    assert stats['fixed_equal'] == probe['stats']['fixed_equal'] == 8184
    assert not stats['fixed_increased'] and not stats['fixed_decreased']
    assert stats['geometry_eligible'] == probe['stats']['geometry_eligible'] == 39572
    assert counts == Counter(bounded=65408, refused_empty_observation=64)
    assert sha(P/'cases_sheng.jsonl') == audit['cases_sha256'] == probe['cases_sha256']
    assert audit['freeze_sha256'] == probe['freeze_sha256'] == sha(E/'freeze.json')
    assert not audit['deployment_authorizations'] and not probe['stats']['deployment_authorized']
    assert audit['checked_fallback_feasibility_witnesses'] == 46 and audit['exact_body_certificates'] == 1536
    for name in ('tests_pre_freeze_local.log', 'tests_sheng.log'):
        t = (P/name).read_text()
        assert 'Ran 7 tests' in t and t.rstrip().endswith('OK')
    if a.prepare:
        sources = dict(frozen['sources'])
        for p in E.iterdir():
            if p.is_file():
                sources[str(p.relative_to(ROOT))] = sha(p)
        sources[REPORT] = sha(ROOT/REPORT)
        write(P/'publication_source_manifest.json', dict(sources=sources, inputs=frozen['inputs'], scope='Frozen pre-replay implementation plus post-result report and packaging; no retuning.'))
        files = {n:dict(bytes=p.stat().st_size, sha256=sha(p)) for n, p in artifacts().items()}
        assert all(v['bytes'] < 100*1024*1024 for v in files.values())
        write(P/'artifact_manifest.json', dict(files=files, file_count=len(files), total_bytes=sum(v['bytes'] for v in files.values()), exclusions=sorted(EXCLUDE)))
    publication = read(P/'publication_source_manifest.json')
    for section in ('sources', 'inputs'):
        verify_hashes(publication[section])
    manifest = read(P/'artifact_manifest.json')
    assert set(artifacts()) == set(manifest['files'])
    assert manifest['file_count'] == len(manifest['files'])
    assert manifest['total_bytes'] == sum(v['bytes'] for v in manifest['files'].values())
    for n, v in manifest['files'].items():
        assert (ROOT/n).stat().st_size == v['bytes'] and sha(ROOT/n) == v['sha256']
    out = dict(files=manifest['file_count'], bytes=manifest['total_bytes'], artifact_manifest_sha256=sha(P/'artifact_manifest.json'), publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'), audit_sha256=sha(P/'audit_sheng.json'), stats=stats, statuses=counts, radius_summary=by_radius, frozen_sources_valid=True, finite_geometry_verification_complete=True, new_policy_or_ego_or_wireless_qualified=False, goal_complete=False)
    if a.out:
        write(a.out, out)
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
