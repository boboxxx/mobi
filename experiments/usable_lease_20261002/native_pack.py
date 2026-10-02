"""Vectorized coverage graph plus two equally compiled established heuristics."""
import ctypes, functools, math, os
import numpy as np
from scipy.spatial import cKDTree
from thin import body
from efficient_renew import packet


@functools.lru_cache(maxsize=1)
def library():
    lib = ctypes.CDLL(os.environ['MOBI_COVER_LIBRARY'])
    func = lib.cover_select
    ptr = np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags='C_CONTIGUOUS')
    func.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.c_int64,
                     ptr, ptr, ptr, ctypes.c_int, ptr]
    func.restype = ctypes.c_int64
    return func


def select(indptr, indices, order, cells, mode):
    indptr, indices, order = (np.ascontiguousarray(x, dtype=np.int64)
                             for x in [indptr, indices, order])
    n = len(indptr) - 1
    if n < 0 or len(order) != n:
        raise ValueError('Invalid graph dimensions')
    out = np.empty(n, dtype=np.int64)
    count = library()(n, cells, len(indices), indptr, indices, order, mode, out)
    if count < 0:
        raise ValueError('Invalid/incomplete coverage graph: ' + str(count))
    return out[:count]


def pack(points, origin, observed, reference, profiles, scope, contract, motion,
         prior, horizon=.4, sequence=0, strategy='greedy'):
    if (strategy not in ['greedy', 'thin'] or type(sequence) is not int
            or sequence < 0 or not math.isfinite(horizon) or horizon <= 0
            or len({p.clock for p in profiles.values()}) != 1):
        raise ValueError('Invalid source metadata/strategy')
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
    candidates = np.asarray(sorted(candidates), dtype=np.int64)
    offset, row_chunks, col_chunks = 0, [], []
    for name, profile in profiles.items():
        cells = body.required(profile, motion, horizon)
        cells = cells[~body.prior_covers(cells, scope, motion, prior, profile, stamp)]
        if not len(cells):
            continue
        result = results[name]
        mask = np.isin(result['ray_indices'], candidates)
        ids = result['ray_indices'][mask]
        w = result['witnesses'][mask] @ body.rotation(motion.yaw)
        radius = profile.r_min - result['error'][mask] - profile.step / math.sqrt(2) - 1e-9
        use = radius > 0
        ids, w, radius = ids[use], w[use], radius[use]
        found = cKDTree(cells).query_ball_point(w, radius)
        lengths = np.fromiter((len(x) for x in found), dtype=np.int64, count=len(found))
        if lengths.sum():
            centers = np.concatenate(found).astype(np.int64, copy=False)
            witnesses = np.repeat(np.arange(len(w)), lengths)
            strict = np.linalg.norm(cells[centers] - w[witnesses], axis=1) < radius[witnesses]
            row_chunks.append(np.searchsorted(candidates, ids[witnesses[strict]]))
            col_chunks.append(offset + centers[strict])
        offset += len(cells)
    if offset:
        rows = np.concatenate(row_chunks)
        cols = np.concatenate(col_chunks)
        order_edges = np.lexsort((cols, rows))
        rows, cols = rows[order_edges], cols[order_edges]
        sizes = np.bincount(rows, minlength=len(candidates))
        indptr = np.concatenate(([0], np.cumsum(sizes)))
        if strategy == 'thin':
            costs = np.asarray([len(body.canonical(r[i].tolist())) + 1 for i in candidates])
            priority = np.lexsort((candidates, -costs / np.maximum(1, sizes)))
        else:
            priority = np.arange(len(candidates))
        chosen = candidates[select(indptr, cols, priority, offset,
                                   0 if strategy == 'thin' else 1)]
    else:
        chosen = np.asarray([0], dtype=np.int64) if len(r) else np.empty(0, dtype=np.int64)
    if not len(chosen) or len(chosen) > body.MAX_RAYS:
        return None
    blob = packet(o, r[chosen], ref, profiles, scope, contract, motion, prior,
                  horizon, sequence)
    return blob if body.verify(blob, profiles, scope, contract, motion, prior,
                               stamp, 0) else None
