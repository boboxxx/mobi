"""Extend coverage using only new unknown cells and uncertainty-checked rays.

The old template is never evidence: it proposes indices into CURRENT raw rays.
Current base rays and receiver-owned history cover the interior; added current
rays cover a disjoint per-class gap universe. The receiver still fully checks.
"""
import math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'online_evidence_20261002'))
from efficient_renew import body, propose, missing_cells, packet
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'usable_lease_20261002'))
from native_pack import select


def gap_candidates(results, profiles, motion, gaps):
    chosen = set()
    for name, profile in profiles.items():
        cells = gaps[name]
        missing = np.ones(len(cells), dtype=bool)
        result = results[name]
        w = result['witnesses'] @ body.rotation(motion.yaw)
        for error in np.unique(result['error']):
            radius = profile.r_min - error - profile.step / math.sqrt(2) - 1e-9
            if radius <= 0:
                continue
            todo = np.flatnonzero(missing)
            if not len(todo):
                break
            group = np.flatnonzero(result['error'] == error)
            d, j = cKDTree(w[group]).query(cells[todo], k=1)
            hit = d < radius
            chosen.update(result['ray_indices'][group[j[hit]]].tolist())
            missing[todo[hit]] = False
        if missing.any():
            return None
    return np.asarray(sorted(chosen), dtype=np.int64)


def greedy_gaps(results, profiles, motion, gaps, candidates):
    offset, rows, cols = 0, [], []
    for name, profile in profiles.items():
        cells = gaps[name]
        if not len(cells):
            continue
        result = results[name]
        use = np.isin(result['ray_indices'], candidates)
        ids = result['ray_indices'][use]
        w = result['witnesses'][use] @ body.rotation(motion.yaw)
        radius = profile.r_min - result['error'][use] - profile.step / math.sqrt(2) - 1e-9
        use = radius > 0
        ids, w, radius = ids[use], w[use], radius[use]
        found = cKDTree(cells).query_ball_point(w, radius)
        lengths = np.fromiter((len(x) for x in found), dtype=np.int64, count=len(found))
        if lengths.sum():
            centers = np.concatenate(found).astype(np.int64, copy=False)
            witnesses = np.repeat(np.arange(len(w)), lengths)
            strict = np.linalg.norm(cells[centers] - w[witnesses], axis=1) < radius[witnesses]
            rows.append(np.searchsorted(candidates, ids[witnesses[strict]]))
            cols.append(offset + centers[strict])
        offset += len(cells)
    if not offset:
        return np.empty(0, dtype=np.int64)
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    order = np.lexsort((cols, rows))
    rows, cols = rows[order], cols[order]
    sizes = np.bincount(rows, minlength=len(candidates))
    indptr = np.concatenate(([0], np.cumsum(sizes)))
    return candidates[select(indptr, cols, np.arange(len(candidates)), offset, 1)]


def repair(template, points, origin, observed, reference, profiles, scope,
           contract, motion, prior, horizon=.4, sequence=0, strategy='nearest',
           diagnostics=None):
    if diagnostics is not None:
        diagnostics.clear()
        diagnostics.update(branch='rejected', base_rays=0, gaps={}, candidate_rays=0, added_rays=0)
    try:
        if (strategy not in ['nearest', 'greedy'] or type(sequence) is not int
                or sequence < 0 or not math.isfinite(horizon)
                or math.floor(horizon * body.TIME_SCALE) <= 0
                or len({p.clock for p in profiles.values()}) != 1
                or any(p.error != 0 for p in profiles.values())):
            return None
        if template is None:
            return None
        proposal = propose(template, points, origin, observed, reference,
                           profiles, scope, contract, motion)
        if proposal is None:
            return None
        o, r, ref, _, _, base = proposal
        if not len(base) or len(base) > body.MAX_RAYS:
            return None
        results = body.projections(o, r[base], ref, profiles, scope, contract)
        gaps = {name: missing_cells(results[name], profile, scope, motion, prior,
                                     ref / body.TIME_SCALE, horizon)
                for name, profile in profiles.items()}
        if any(g is None for g in gaps.values()):
            return None
        if diagnostics is not None:
            diagnostics.update(base_rays=len(base), gaps={n: len(g) for n, g in gaps.items()})
        if not any(len(g) for g in gaps.values()):
            chosen, added, candidates = base, np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        else:
            results = body.projections(o, r, ref, profiles, scope, contract)
            candidates = gap_candidates(results, profiles, motion, gaps)
            if candidates is None:
                return None
            added = (greedy_gaps(results, profiles, motion, gaps, candidates)
                     if strategy == 'greedy' else candidates)
            chosen = np.unique(np.concatenate([base, added]))
        if len(chosen) > body.MAX_RAYS:
            return None
        blob = packet(o, r[chosen], ref, profiles, scope, contract, motion, prior,
                      horizon, sequence)
        if diagnostics is not None:
            diagnostics.update(branch='base' if not len(added) else 'patched',
                               candidate_rays=len(candidates), added_rays=len(np.setdiff1d(chosen, base)))
        return blob
    except (ValueError, TypeError, KeyError, OverflowError, IndexError):
        return None
