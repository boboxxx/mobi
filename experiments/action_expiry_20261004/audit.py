"""Independent integer/Fraction geometry and source-age checks; no new risk claim."""
import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = Path(__file__).resolve().parent
P = ROOT/'results'/E.name
DIRECTIONS = json.loads((ROOT/'experiments/pose_support_20261004/directions.json').read_bytes())['normal_xy']


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def up(x):
    return (x.numerator+x.denominator-1)//x.denominator


def ceilroot(n):
    r = math.isqrt(n)
    return r+(r*r < n)


def radius(extent):
    n = sum((F.from_float(float(v))*1000000)**2 for v in extent)
    return ceilroot(n.numerator//n.denominator) if n.denominator == 1 else math.isqrt(n.numerator//n.denominator)+(math.isqrt(n.numerator//n.denominator)**2 < n)


def rectangles(hulls, extent, delta):
    body, xy = radius(extent), radius(extent[:2])
    pad = (body*87267+999999)//1000000 + (xy*8730+999999)//1000000 + 8000+delta
    a, b = [up(F.from_float(float(v))*1000000)+pad for v in extent[:2]]
    out = []
    for group in hulls:
        pts = [[v*10000 for v in p] for p in group]
        for c, s in DIRECTIONS:
            norm = c*c+s*s
            projections = [(c*x+s*y, -s*x+c*y) for x, y in pts]
            bound = [max(p[0] for p in projections)-a*ceilroot(norm), min(p[0] for p in projections)+a*ceilroot(norm), max(p[1] for p in projections)-b*ceilroot(norm), min(p[1] for p in projections)+b*ceilroot(norm)]
            if bound[0] <= bound[1] and bound[2] <= bound[3]:
                out.append((c, s, norm, bound))
    return out


def rect_distance(rect, point):
    c, s, norm, (a, b, z, w) = rect
    u, v = c*point[0]+s*point[1], -s*point[0]+c*point[1]
    return F(max(a-u, 0, u-b)**2+max(z-v, 0, v-w)**2, norm)


def inrect(rect, point):
    c, s, _, (a, b, z, w) = rect
    u, v = c*point[0]+s*point[1], -s*point[0]+c*point[1]
    return a <= u <= b and z <= v <= w


def feasible(point, centers, r):
    return all(sum((point[k]-c[k])**2 for k in (0, 1)) <= r*r for c in centers)


def body_proof(proof, centers, query, r):
    kind = proof['kind']
    if kind in ('empty', 'singleton'):
        ids, weights = proof['indices'], proof['weights']
        assert len(ids) == len(weights) and min(weights) >= 0 and sum(weights) > 0
        cc = [centers[i] for i in ids]
        W = sum(weights)
        p = [sum(w*c[k] for w, c in zip(weights, cc)) for k in (0, 1)]
        gap = W*sum(w*sum(x*x for x in c) for w, c in zip(weights, cc))-sum(x*x for x in p)-W*W*r*r
        assert proof['variance_gap'] == gap
        if kind == 'empty':
            assert gap > 0
            return None
        assert gap == 0
        pt = [F(x, W) for x in p]
        assert feasible(pt, centers, r)
        d = sum((pt[k]-query[k])**2 for k in (0, 1))
        lower = math.isqrt(d.numerator//d.denominator)
    elif kind == 'inside':
        assert feasible(query, centers, r)
        lower = 0
    else:
        assert kind == 'dual'
        pt = [F(v, 1000000) for v in proof['point']]
        assert feasible(pt, centers, r)
        ids, weights = proof['indices'], proof['weights']
        assert ids and len(ids) == len(weights) and min(weights) >= 0
        vectors = [[proof['point'][k]-centers[i][k]*1000000 for k in (0, 1)] for i in ids]
        u = [-sum(w*v[k] for w, v in zip(weights, vectors)) for k in (0, 1)]
        if not any(u):
            lower = 0
        else:
            numerator = sum(w*(sum(v[k]*(query[k]-centers[i][k]) for k in (0, 1))*1000000-r*ceilroot(sum(x*x for x in v)*10**12)) for i, w, v in zip(ids, weights, vectors))
            lower = max(0, numerator//ceilroot(sum(x*x for x in u)*10**12))
    assert proof['lower_um'] == lower
    return lower


def safe(distance, body, query_radius, t):
    return F(distance)-body-query_radius > F(5000000*t, 1000000)+F(3000000*t*t, 2*10**12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    f = json.loads((E/'freeze.json').read_bytes())
    for section in ('sources', 'inputs'):
        for n, h in f[section].items():
            assert sha(ROOT/n) == h, n
    fixture = ROOT/'results/prospective_component_20261004/qualification_test_sheng.json'
    d = json.loads(fixture.read_bytes())
    lookup = {r['id']: r for r in d['rows']}
    prep = json.loads((P/'preparation_sheng.json').read_bytes())
    compiled = {}
    witnesses = 0
    for record in prep:
        r = lookup[record['id']]
        family = record['family']
        mode = family[len('component_'):]
        reg = d['registry'][r['blueprint']]
        supported = r['prediction']['status'] == 'supported'
        threshold = F(*reg['supported_'+mode])
        delta = up(threshold*10000) if supported else int(F(*reg['fallback_um']))
        ext = d['catalog'][r['blueprint']]
        rr = rectangles(r['hulls_cm'], ext, delta) if r['hulls_cm'] else []
        body = radius(ext)
        centers = ([r['prediction']['mean_um']] if mode == 'mean' else r['prediction']['centers_um']) if supported else []
        radius_um = up(threshold*r['prediction']['single_scale_um' if mode == 'mean' else 'modes_scale_um']) if supported else body+8000+delta
        groups = [[[v*10000 for v in point] for point in group] for group in r['hulls_cm']]
        covered = F(*r['scores']['supported_'+mode]) <= threshold and F(*r['scores']['fallback_um']) <= F(*reg['fallback_um'])
        truth = [F.from_float(float(v))*1000000 for v in r['true_xy']]
        if covered and r['hulls_cm']:
            assert any(inrect(rect, truth) for rect in rr)
            assert (any(sum((truth[k]-c[k])**2 for k in (0, 1)) <= radius_um**2 for c in centers) if supported else any(feasible(truth, group, radius_um) for group in groups))
        if record['witness'] is not None:
            w = record['witness']
            pt = [F(v, w['point_den']) for v in w['point_num']]
            assert any(inrect(rect, pt) for rect in rr) and any(feasible(pt, group, radius_um) for group in groups)
            witnesses += 1
        if record['status'] == 'refused_disjoint_supported_sets':
            assert supported and not any(rect_distance(rect, c) <= radius_um**2 for rect in rr for c in centers)
        compiled[record['id'], family] = (rr, centers, groups, radius_um, body, covered, truth)
    count = covered_checks = certificate_checks = 0
    with (P/'cases_sheng.jsonl').open() as stream:
        for line in stream:
            case = json.loads(line)
            r = lookup[case['id']]
            proposal, gate = case['proposal'], case['gate']
            rr, centers, groups, radius_um, body, covered, truth = compiled[case['id'], case['family']]
            assert proposal['source_us'] == r['source_us'] and not proposal['risk_certificate_applicable'] and not proposal['deployment_authorized'] and not gate['deployment_authorized']
            age = proposal['lower_us']
            assert proposal['proposal_valid_until_us'] == r['source_us']+age
            assert gate['geometry_eligible'] == (proposal['status'] == 'bounded' and r['source_us']+270000 <= proposal['proposal_valid_until_us'])
            if proposal['status'] == 'bounded':
                query = proposal['query_um']
                dist = min(rect_distance(rect, query) for rect in rr)
                lower_pose = math.isqrt(dist.numerator//dist.denominator)
                if centers:
                    other = min(max(0, math.isqrt(sum((c[k]-query[k])**2 for k in (0, 1)))-radius_um) for c in centers)
                else:
                    proofs = proposal['body_proofs']
                    assert len(proofs) == len(groups)
                    vals = [body_proof(proof, group, query, radius_um) for proof, group in zip(proofs, groups)]
                    other = min(v for v in vals if v is not None)
                    certificate_checks += len(proofs)
                lower = max(lower_pose, other)
                assert proposal['distance_lower_um'] == lower
                qr = proposal['query_radius_um']
                assert 0 <= age <= 500000
                if age:
                    assert safe(lower, body, qr, age)
                if age < 500000:
                    assert not safe(lower, body, qr, age+1)
                if covered:
                    actual_squared = sum((truth[k]-query[k])**2 for k in (0, 1))
                    assert lower*lower <= actual_squared
                    if age:
                        reach = F(body+qr)+F(5000000*age, 1000000)+F(3000000*age*age, 2*10**12)
                        assert reach*reach < actual_squared
                    covered_checks += 1
            else:
                assert age == 0
            count += 1
    assert count == 65472
    result = dict(queries=count, covered_geometric_queries=covered_checks, exact_body_certificates=certificate_checks, checked_fallback_feasibility_witnesses=witnesses, deployment_authorizations=0, cases_sha256=sha(P/'cases_sheng.jsonl'), fixture_sha256=sha(fixture), freeze_sha256=sha(E/'freeze.json'), scope='Independent exact geometry regression; no new policy certificate, new scene data or ego/wireless result.', goal_complete=False)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('FINITE_INDEPENDENT_ACTION_QUERY_AUDIT_COMPLETE', count, flush=True)


if __name__ == '__main__':
    main()
