"""Exact, conditional set-membership reference. Runtime API accepts no truth.

Position micrometres; velocity micrometres/second; times microseconds.
Two independent planar outer sets retain position/velocity correlation within
each axis. This is a reference implementation, not a WCET or coverage claim.
"""
from fractions import Fraction as F

SPEED = 5000000
ACCEL = 3000000
CAP = 500000
ACTION = 300000
QUERY_RADIUS = 2500000
HISTORY = 7


def clip(poly, a, b, c):
    """Intersect a convex polygon with a*p+b*v <= c, exactly."""
    if not poly:
        return []
    out = []
    for start, end in zip(poly, poly[1:] + poly[:1]):
        fs = a*start[0] + b*start[1] - c
        fe = a*end[0] + b*end[1] - c
        if fs <= 0:
            out.append(start)
        if (fs < 0 < fe) or (fe < 0 < fs):
            lam = fs/(fs-fe)
            out.append(tuple(start[k]+lam*(end[k]-start[k]) for k in (0, 1)))
    return list(dict.fromkeys(out))


def infer(history):
    """Each observation: (source_us, [[xlo,xhi],[ylo,yhi]]) or None.

    All observations in the window must be usable. Missing/empty sets refuse;
    they are never treated as evidence that the road is empty.
    """
    history = history[-HISTORY:]
    if not history or any(bounds is None for _, bounds in history):
        return None
    stamps = [t for t, _ in history]
    if any(type(t) is not int or t < 0 for t in stamps):
        raise ValueError('invalid source epoch')
    if any(a >= b for a, b in zip(stamps, stamps[1:])):
        raise ValueError('source epochs must strictly increase')
    source = stamps[-1]
    polygons = []
    for axis in (0, 1):
        lo, hi = map(F, history[-1][1][axis])
        if lo > hi:
            return None
        poly = [(lo, F(-SPEED)), (hi, F(-SPEED)),
                (hi, F(SPEED)), (lo, F(SPEED))]
        for stamp, bounds in history:
            dt = F(source-stamp, 1000000)
            pad = F(ACCEL, 2)*dt*dt
            lower, upper = map(F, bounds[axis])
            if lower > upper:
                return None
            poly = clip(poly, F(1), -dt, upper+pad)
            poly = clip(poly, F(-1), dt, -lower+pad)
        if not poly:
            return None
        polygons.append(poly)
    return polygons


def factorize(polygons):
    if polygons is None:
        return None
    out = []
    for poly in polygons:
        plo, phi = min(p[0] for p in poly), max(p[0] for p in poly)
        vlo, vhi = min(p[1] for p in poly), max(p[1] for p in poly)
        out.append([(plo, vlo), (phi, vlo), (phi, vhi), (plo, vhi)])
    return out


def contains(polygons, position, velocity):
    """Audit helper; never called by inference or expiry."""
    if polygons is None:
        return False
    for poly, p, v in zip(polygons, position, velocity):
        point = (F(p), F(v))
        if len(poly) < 3:
            # Degenerate sets are accepted only at their exact vertices.
            if point not in poly:
                return False
            continue
        for a, b in zip(poly, poly[1:]+poly[:1]):
            if (b[0]-a[0])*(point[1]-a[1]) - (b[1]-a[1])*(point[0]-a[0]) < 0:
                return False
    return True


def margin(poly, sign, q, radius, age_us):
    dt = F(age_us, 1000000)
    return min(sign*(p+dt*v-q) for p, v in poly)-radius-F(ACCEL, 2)*dt*dt


def expiry(polygons, query, target_radius):
    """Strict separation on one fixed axis for every t in [0, expiry].

    For a fixed vertex/direction its gap is a concave quadratic; their minimum
    is concave. Positive endpoints therefore imply a positive whole prefix.
    It is sufficient, not a complete collision-free trajectory test.
    """
    if polygons is None:
        return 0
    radius = target_radius+QUERY_RADIUS
    best = 0
    for poly, q in zip(polygons, query):
        for sign in (-1, 1):
            if margin(poly, sign, q, radius, 0) <= 0:
                continue
            if margin(poly, sign, q, radius, CAP) > 0:
                best = CAP
                continue
            lo, hi = 0, CAP
            while lo+1 < hi:
                mid = (lo+hi)//2
                if margin(poly, sign, q, radius, mid) > 0:
                    lo = mid
                else:
                    hi = mid
            best = max(best, lo)
    return best


def permit(source_us, expiry_us, use_us):
    return source_us <= use_us and use_us+ACTION <= source_us+expiry_us


def encode(polygons):
    return None if polygons is None else [
        [[[x.numerator, x.denominator] for x in vertex] for vertex in poly]
        for poly in polygons]
