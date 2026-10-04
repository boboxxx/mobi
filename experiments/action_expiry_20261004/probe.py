"""Finite deterministic regression replay; all changed/refused proposals retained."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from query_kernel import Evidence, decision

ROOT = Path(__file__).resolve().parents[2]
E = Path(__file__).resolve().parent
P = ROOT/'results'/E.name
FAMILIES = ('component_mean', 'component_modes')
QUERIES = [([-6000000, 0], 750000), ([6000000, 0], 750000)] + [
    ([x*1000000, 2000000], r) for x in (-9, -6, -3, 0, 3, 6, 9) for r in (750000, 2500000)]


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def check_freeze():
    f = json.loads((E/'freeze.json').read_bytes())
    for section in ('sources', 'inputs'):
        for name, digest in f[section].items():
            assert sha(ROOT/name) == digest, name


def main():
    check_freeze()
    out = P/'cases_sheng.jsonl'
    assert not out.exists() and not (P/'probe_sheng.json').exists()
    fixture = ROOT/'results/prospective_component_20261004/qualification_test_sheng.json'
    d = json.loads(fixture.read_bytes())
    assert len(d['rows']) == 2046
    stats = Counter()
    preparation = []
    with out.open('x') as stream:
        for index, r in enumerate(d['rows']):
            for family in FAMILIES:
                reg = d['registry'][r['blueprint']]
                thresholds = dict(supported=Fraction(*reg['supported_'+family[len('component_'):]]), fallback_um=int(Fraction(*reg['fallback_um'])))
                evidence = Evidence(r['hulls_cm'], d['catalog'][r['blueprint']], r['prediction'], thresholds, family, r['source_us'])
                preparation.append(dict(id=r['id'], family=family, status=evidence.status, witness=evidence.witness))
                stats['preparation:'+evidence.status] += 1
                for j, (query, radius) in enumerate(QUERIES):
                    proposal = evidence.query(query, radius)
                    gate = decision(proposal, r['source_us']+50000, 220000)
                    baseline = r['geometries'][family]
                    old = (baseline['lower_us'][j] if baseline['status'] == 'bounded' else 0) if j < 2 else None
                    if old is not None:
                        stats['fixed_equal' if proposal['lower_us'] == old else 'fixed_increased' if proposal['lower_us'] > old else 'fixed_decreased'] += 1
                    stats['queries'] += 1
                    stats['geometry_eligible'] += gate['geometry_eligible']
                    stats['deployment_authorized'] += gate['deployment_authorized']
                    stream.write(json.dumps(dict(id=r['id'], family=family, query_index=j, proposal=proposal, gate=gate, historical_lower_us=old), separators=(',', ':'))+'\n')
            if (index+1) % 500 == 0:
                print('compiled and queried', index+1, flush=True)
    assert stats['queries'] == 65472 and not stats['deployment_authorized']
    (P/'preparation_sheng.json').write_text(json.dumps(preparation, separators=(',', ':'))+'\n')
    result = dict(stats=stats, source_frames=2046, cases_sha256=sha(out), fixture_sha256=sha(fixture), freeze_sha256=sha(E/'freeze.json'), scope='Deterministic regression fixture replay, no new statistical qualification or ego control.', goal_complete=False)
    (P/'probe_sheng.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('FINITE_ACTION_QUERY_REGRESSION_COMPLETE', dict(stats), flush=True)


if __name__ == '__main__':
    main()
