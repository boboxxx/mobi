"""Maximal horizon of the existing fixed-region tile certificate, not true safety.

Unexcluded cells stay possible; no inference from absent detections. Compute
coverage once on the whole bounded domain, then invert monotone reachability.
"""
import math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'body_evidence_20261001'))
import body
from geometry import grid, travel


def class_frontier(result, profile, scope, motion, prior, reference, cap_us):
    if any(x != 0 for x in [motion.vx, motion.vy, motion.acceleration, motion.yaw_rate]):
        raise ValueError('Only a fixed region is supported')
    if type(cap_us) is not int or cap_us < 1:
        raise ValueError('Positive integer horizon cap required')
    cells, _ = grid(profile.domain, profile.step)
    missing = ~body.prior_covers(cells, scope, motion, prior, profile, reference)
    witnesses = result['witnesses'] @ body.rotation(motion.yaw)
    for error in np.unique(result['error']):
        radius = profile.r_min - error - profile.step / math.sqrt(2) - 1e-9
        if radius <= 0:
            continue
        todo = np.flatnonzero(missing)
        if not len(todo):
            break
        near = cKDTree(witnesses[result['error'] == error]).query(cells[todo], k=1)[0]
        missing[todo[near < radius]] = False
    low, high, margin = body.envelope(motion, 0, profile.clock)
    unknown = cells[missing]
    distances = body.box_distance(unknown, low, high)
    index = int(np.argmin(distances)) if len(distances) else None
    nearest = float(distances[index]) if index is not None else math.inf
    extent = np.maximum(np.abs(low), np.abs(high))

    def passes(h_us):
        inflate = margin + profile.r_max + travel(h_us / body.TIME_SCALE + profile.clock, profile)
        return bool(np.all(extent + inflate < profile.domain) and
                    nearest > inflate + profile.step / math.sqrt(2))

    lo, hi = 0, cap_us + 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if passes(mid):
            lo = mid
        else:
            hi = mid
    assert lo == 0 or passes(lo)
    assert lo == cap_us or not passes(lo + 1)
    return dict(horizon_us=lo, cap_limited=lo == cap_us,
                nearest_unexcluded_cell=unknown[index].tolist() if index is not None else None,
                nearest_unexcluded_distance_m=nearest if math.isfinite(nearest) else None,
                unexcluded_cells=int(missing.sum()))


def frontier(results, profiles, scope, motion, prior, reference, cap_us=2_000_000):
    classes = {n: class_frontier(results[n], p, scope, motion, prior, reference, cap_us)
               for n, p in profiles.items()}
    h = min(v['horizon_us'] for v in classes.values())
    return dict(horizon_us=h, classes=classes,
                limiting_classes=[n for n, v in classes.items() if v['horizon_us'] == h])


def root_ready(reference_us, horizon_us, available_s, next_tick_s=.05):
    """Reserve a strictly valid next encoded observation; never alter expiry."""
    if not all(math.isfinite(x) for x in [available_s, next_tick_s]) or next_tick_s < 0:
        raise ValueError('Invalid next observation time')
    return math.ceil((available_s + next_tick_s) * body.TIME_SCALE) < reference_us + horizon_us
