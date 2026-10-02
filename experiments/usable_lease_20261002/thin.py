"""Coverage-preserving reverse deletion, with a complete unchanged receiver.

This constructs an inclusion-minimal cover of the nearest-support candidate
set, not a minimum-byte cover of all observed rays. Empty cells stay unknown.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'online_evidence_20261002'))
from efficient_renew import body, packet


def delete_redundant(neighborhoods, costs, cells):
    """Input neighborhoods must contain unique indices. Never lose a cell."""
    if type(cells) is not int or cells < 0:
        raise ValueError('Invalid universe')
    counts = np.zeros(cells, dtype=np.int64)
    for near in neighborhoods.values():
        if np.any(near < 0) or np.any(near >= cells) or len(np.unique(near)) != len(near):
            raise ValueError('Invalid cover indices')
        counts[near] += 1
    if cells and np.any(counts == 0):
        raise ValueError('Incomplete candidate cover')
    kept = set(neighborhoods)
    # Prefer removing expensive rays with few covered cells. Deterministic ties.
    order = sorted(kept, key=lambda i: (-costs[i] / max(1, len(neighborhoods[i])), i))
    for i in order:
        near = neighborhoods[i]
        if np.all(counts[near] >= 2):
            counts[near] -= 1
            kept.remove(i)
    assert not cells or np.all(counts >= 1)
    assert all(np.any(counts[neighborhoods[i]] == 1) for i in kept)
    return sorted(kept)


def pack(points, origin, observed, reference, profiles, scope, contract, motion,
         prior, horizon=.4, sequence=0):
    if (type(sequence) is not int or sequence < 0 or not math.isfinite(horizon)
            or horizon <= 0 or len({p.clock for p in profiles.values()}) != 1):
        raise ValueError('Invalid source metadata')
    o, r, ref = body.encode_source(points, origin, observed, reference)
    stamp = ref / body.TIME_SCALE
    results = body.projections(o, r, ref, profiles, scope, contract)
    candidates = set()
    for name, profile in profiles.items():
        ok, ids = body.coverage(results[name], profile, scope, motion, horizon,
                                prior, stamp, True)
        if not ok:
            return None
        candidates.update(ids)
    if not candidates:
        if not len(r):
            return None
        candidates = {0}  # Wire schema retains an actual ray for history-only cover.
    neighbors = {i: [] for i in candidates}
    offset = 0
    for name, profile in profiles.items():
        cells = body.required(profile, motion, horizon)
        cells = cells[~body.prior_covers(cells, scope, motion, prior, profile, stamp)]
        if not len(cells):
            continue
        result = results[name]
        mask = np.isin(result['ray_indices'], sorted(candidates))
        ids = result['ray_indices'][mask]
        w = result['witnesses'][mask] @ body.rotation(motion.yaw)
        radius = profile.r_min - result['error'][mask] - profile.step / math.sqrt(2) - 1e-9
        use = radius > 0
        tree = cKDTree(cells)
        for i, witness, rad, near in zip(ids[use], w[use], radius[use],
                                        tree.query_ball_point(w[use], radius[use])):
            near = np.asarray(near, dtype=np.int64)
            # query_ball_point is inclusive; the original coverage is strict.
            near = near[np.linalg.norm(cells[near] - witness, axis=1) < rad]
            neighbors[int(i)].extend((offset + near).tolist())
        offset += len(cells)
    neighborhoods = {i: np.unique(np.asarray(v, dtype=np.int64)) for i, v in neighbors.items()}
    costs = {i: len(body.canonical(r[i].tolist())) + 1 for i in candidates}
    chosen = delete_redundant(neighborhoods, costs, offset)
    if not chosen:
        chosen = [0]
    if len(chosen) > body.MAX_RAYS:
        return None
    blob = packet(o, r[chosen], ref, profiles, scope, contract, motion, prior,
                  horizon, sequence)
    return blob if body.verify(blob, profiles, scope, contract, motion, prior,
                               stamp, 0) else None
