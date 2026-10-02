"""Compute common geometric bounds once; preserve class-wise motion and bins.

Expressions and floating operation order mirror proof.projections and
projection.bounded_witnesses. The original receiver still uses those originals.
"""
import numpy as np
from patch import body
from proof import QUANTUM


def projections(origins_q, rays, reference_us, profiles, scope, contract):
    ages = (reference_us - rays[:, 4]) / body.TIME_SCALE
    if np.any(ages < 0) or np.any(ages > contract.max_ray_age):
        raise ValueError('Invalid ray ages')
    o = origins_q[rays[:, 0]] * QUANTUM
    p = rays[:, 1:4] * QUANTUM
    q = np.asarray(scope.query, dtype=float)
    pe = np.broadcast_to(np.asarray(contract.point_error + QUANTUM / 2, dtype=float), p.shape)
    oe = np.broadcast_to(np.asarray(contract.origin_error + QUANTUM / 2, dtype=float), p.shape)
    qe = np.broadcast_to(np.asarray(contract.query_error, dtype=float), (2,))
    if not np.isfinite(p).all() or not np.isfinite(o).all() or not np.isfinite(q).all():
        raise ValueError('Invalid coordinates')
    valid = (o[:, 2] - oe[:, 2] > scope.plane_z + 1e-9) & (p[:, 2] + pe[:, 2] < scope.plane_z - 1e-9)
    ids = np.flatnonzero(valid)
    p, o, pe, oe, age = p[ids], o[ids], pe[ids], oe[ids], ages[ids]
    pl, pu, ol, ou = p - pe, p + pe, o - oe, o + oe
    tl = (ol[:, 2] - scope.plane_z) / (ol[:, 2] - pl[:, 2])
    tu = (ou[:, 2] - scope.plane_z) / (ou[:, 2] - pu[:, 2])
    t = (o[:, 2] - scope.plane_z) / (o[:, 2] - p[:, 2])
    w = (1 - t[:, None]) * o[:, :2] + t[:, None] * p[:, :2] - q
    low = np.minimum((1 - tl[:, None]) * ol[:, :2] + tl[:, None] * pl[:, :2],
                     (1 - tu[:, None]) * ol[:, :2] + tu[:, None] * pl[:, :2]) - q - qe
    high = np.maximum((1 - tl[:, None]) * ou[:, :2] + tl[:, None] * pu[:, :2],
                      (1 - tu[:, None]) * ou[:, :2] + tu[:, None] * pu[:, :2]) - q + qe
    position = np.linalg.norm(np.maximum(np.abs(w - low), np.abs(high - w)), axis=1)
    pad = 1e-9 + 64 * np.finfo(float).eps * (1 + np.max(np.abs(np.column_stack([p, o])), axis=1))
    outputs = {}
    for name, profile in profiles.items():
        motion = profile.speed * age + .5 * profile.acceleration * age ** 2
        # Do not combine position+pad first: changed association can change bins.
        error = position + motion + pad
        outputs[name] = dict(witnesses=w.copy(),
                             error=np.ceil(error / contract.error_bin) * contract.error_bin,
                             projection_error=(position + pad).copy(),
                             motion_error=motion, ray_indices=ids.copy())
    return outputs
