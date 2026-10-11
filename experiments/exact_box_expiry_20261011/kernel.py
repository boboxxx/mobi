"""Exact continuous prefix of an affine box plus a growing Euclidean ball.

The source-state box and motion contract are conditional inputs, not inferred
confidence guarantees. This computes the sharp prefix of this outer model,
not of all physically feasible trajectories or of raw partial observations.
All polynomial predicates are rational; touching is unsafe.
"""
from fractions import Fraction as F


def trim(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return p


def value(p, x):
    result = F(0)
    for c in reversed(p):
        result = result*x+c
    return result


def remainder(a, b):
    a, b = trim(a), trim(b)
    assert b
    while len(a) >= len(b):
        factor, offset = a[-1]/b[-1], len(a)-len(b)
        for i, c in enumerate(b):
            a[offset+i] -= factor*c
        a = trim(a)
    return a


def sturm(p):
    p = trim([F(c) for c in p])
    if not p:
        return []
    sequence = [p]
    derivative = trim([i*c for i, c in enumerate(p)][1:])
    if derivative:
        sequence.append(derivative)
    while len(sequence) > 1:
        rem = [-c for c in remainder(sequence[-2], sequence[-1])]
        if not rem:
            break
        sequence.append(rem)
    return sequence


def variations(sequence, x):
    signs = [1 if v > 0 else -1 for p in sequence for v in [value(p, x)] if v]
    return sum(a != b for a, b in zip(signs, signs[1:]))


def positive_interval(sequence, lo, hi):
    assert lo <= hi
    if not sequence or value(sequence[0], lo) <= 0 or value(sequence[0], hi) <= 0:
        return False
    # Nonzero endpoints: Sturm counts every distinct interior root,
    # including even-multiplicity tangencies that do not change sign.
    return variations(sequence, lo) == variations(sequence, hi)


def longest_prefix(regions, cap):
    def safe(end):
        for lo, hi, sequence in regions:
            if lo > end:
                break
            if not positive_interval(sequence, lo, min(hi, F(end))):
                return False
        return True
    if not safe(0):
        return 0
    if safe(cap):
        return cap
    lo, hi = 0, cap
    while lo+1 < hi:
        mid = (lo+hi)//2
        if safe(mid):
            lo = mid
        else:
            hi = mid
    assert safe(lo) and not safe(lo+1)
    return lo


def regions_for_box(state, query, radius, cap, acceleration=3, jump=F(3, 20)):
    """p/radius in micrometers; v in micrometers/s; t in microseconds."""
    assert cap > 0 and radius > 0 and acceleration >= 0 and jump >= 0
    lines, cuts = [], {F(0), F(cap)}
    for (plo, phi, vlo, vhi), q in zip(state, query):
        assert plo <= phi and vlo <= vhi
        low, high = (F(plo)-q, F(vlo, 1000000)), (F(phi)-q, F(vhi, 1000000))
        lines.append((low, high))
        for intercept, slope in (low, high):
            if slope:
                cross = -intercept/slope
                if 0 < cross < cap:
                    cuts.add(cross)
    # Radius = registered target + query + J*t + A*t^2/2.
    radial = [F(radius), F(jump), F(acceleration, 2000000)]
    cuts = sorted(cuts)
    regions = []
    for lo, hi in zip(cuts, cuts[1:]):
        mid = (lo+hi)/2
        polynomial = [F(0)]*5
        for low, high in lines:
            if value(low, mid) > 0:
                gap = low
            elif value(high, mid) < 0:
                gap = tuple(-c for c in high)
            else:
                gap = (F(0), F(0))
            for i, a in enumerate(gap):
                for j, b in enumerate(gap):
                    polynomial[i+j] += a*b
        for i, a in enumerate(radial):
            for j, b in enumerate(radial):
                polynomial[i+j] -= a*b
        regions.append((lo, hi, sturm(polynomial)))
    return regions


def box_prefix(state, query, radius, cap=500000, acceleration=3, jump=F(3, 20)):
    if state is None:
        return 0
    assert len(state) == len(query) == 2
    return longest_prefix(regions_for_box(state, query, radius, cap, acceleration, jump), cap)
