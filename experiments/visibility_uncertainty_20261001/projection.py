"""Bounded ray-plane projection and temporal alignment of empty witnesses.

Input boxes are upstream contracts, not estimates inferred from missing data.
The plane is a fixed, known physical plane. Vertical pose/range uncertainty is
propagated, but uncertainty about whether an object intersects this plane is
not fixed by this module. All accepted rays must be truthful first returns.
"""
import math
import numpy as np


def _box(value, shape, name):
    value = np.broadcast_to(np.asarray(value, dtype=float), shape)
    if not np.isfinite(value).all() or np.any(value < 0):
        raise ValueError('Invalid ' + name)
    return value


def bounded_witnesses(points, origins, query, plane_z, point_error=0.,
                      origin_error=0., query_error=0., ray_age=0.,
                      speed=0., acceleration=0.):
    """Return witnesses, aligned error bounds, and original accepted ray indices.

    XYZ errors are componentwise absolute bounds in the common world frame.
    origins may be a common XYZ vector or one XYZ pose per ray. query_error
    bounds XY query registration. ray_age is measured relative to the chosen
    evidence timestamp, must be nonnegative, and may differ between rays.
    speed bounds obstacle speed at each observation; acceleration bounds its
    subsequent norm. Continuous motion and an opaque inner core are required.

    Returned error includes center-motion uncertainty, so it is an effective
    exclusion-radius debit, not just a measurement-position error.
    """
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError('points must have shape (N,3)')
    o = np.broadcast_to(np.asarray(origins, dtype=float), p.shape)
    q = np.asarray(query, dtype=float)
    if q.shape != (2,) or not np.isfinite(p).all() or not np.isfinite(o).all() or not np.isfinite(q).all():
        raise ValueError('Invalid coordinates')
    if not all(math.isfinite(v) for v in [plane_z, speed, acceleration]) or min(speed, acceleration) < 0:
        raise ValueError('Invalid plane or motion')
    pe = _box(point_error, p.shape, 'point error')
    oe = _box(origin_error, p.shape, 'origin error')
    qe = _box(query_error, (2,), 'query error')
    age = _box(ray_age, (len(p),), 'ray age')
    # Require a crossing strictly before the first return for EVERY input box.
    valid = (o[:, 2] - oe[:, 2] > plane_z + 1e-9) & (p[:, 2] + pe[:, 2] < plane_z - 1e-9)
    idx = np.flatnonzero(valid)
    p, o, pe, oe, age = p[idx], o[idx], pe[idx], oe[idx], age[idx]
    pl, pu, ol, ou = p-pe, p+pe, o-oe, o+oe
    # t=(oz-z)/(oz-pz) is increasing in both oz and pz when oz>z>pz.
    tl = (ol[:,2]-plane_z)/(ol[:,2]-pl[:,2])
    tu = (ou[:,2]-plane_z)/(ou[:,2]-pu[:,2])
    t = (o[:,2]-plane_z)/(o[:,2]-p[:,2])
    w = (1-t[:,None])*o[:,:2]+t[:,None]*p[:,:2]-q
    low = np.minimum((1-tl[:,None])*ol[:,:2]+tl[:,None]*pl[:,:2],
                     (1-tu[:,None])*ol[:,:2]+tu[:,None]*pl[:,:2])-q-qe
    high = np.maximum((1-tl[:,None])*ou[:,:2]+tl[:,None]*pu[:,:2],
                      (1-tu[:,None])*ou[:,:2]+tu[:,None]*pu[:,:2])-q+qe
    position_bound = np.linalg.norm(np.maximum(np.abs(w-low), np.abs(high-w)), axis=1)
    # Small numerical padding; this is float64 code, not a formal interval library.
    pad = 1e-9 + 64*np.finfo(float).eps*(1+np.max(np.abs(np.column_stack([p,o])),axis=1))
    motion_bound = speed*age + .5*acceleration*age**2
    effective_bound = position_bound + motion_bound + pad
    return dict(witnesses=w, error=effective_bound, projection_error=position_bound+pad,
                motion_error=motion_bound, ray_indices=idx)


def select_for_profile(result, error_budget):
    """Use the existing receiver-agreed error budget; never enlarge it silently."""
    if not math.isfinite(error_budget) or error_budget < 0:
        raise ValueError('Invalid error budget')
    return result['witnesses'][result['error'] <= error_budget]
