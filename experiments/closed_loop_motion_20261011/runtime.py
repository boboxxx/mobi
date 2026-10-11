"""Observable fixed-policy runtime; exact arithmetic, no target truth inputs."""
import hashlib
import importlib.util
import json
import math
import zlib
from fractions import Fraction as F
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('closed_motion_geometry', ROOT/'experiments/joint_motion_expiry_20261011/adapter.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
ACTION = 300000
CAP = 500000
RADIUS = 2500000
BUDGET = 20000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extrema(history):
    history = history[-7:]
    if not history or any(b is None for t, b in history):
        return None
    assert all(a[0] < b[0] for a, b in zip(history, history[1:]))
    source = history[-1][0]
    result = []
    for axis in (0, 1):
        lower, upper = [], []
        for stamp, bounds in history:
            dt = F(source-stamp, 1000000)
            pad = 1500000*dt*dt+150000*dt
            lower.append((F(bounds[axis][0])-pad, dt))
            upper.append((F(bounds[axis][1])+pad, dt))
        vlo, vhi = F(-5000000), F(5000000)
        for lo, dl in lower:
            for hi, du in upper:
                a, b = du-dl, lo-hi
                if a == 0 and b > 0:
                    return None
                if a > 0:
                    vlo = max(vlo, b/a)
                if a < 0:
                    vhi = min(vhi, b/a)
        if vlo > vhi:
            return None
        result.append([max(lo+d*vlo for lo, d in lower),
                       min(hi+d*vhi for hi, d in upper), vlo, vhi])
    return result


def root_up(n):
    s = math.isqrt(n)
    return s+(s*s < n)


def prefix(c, b, a):
    """Largest integer t<=CAP with c+b*t-a*t*t>0, given c>0,a>=0."""
    c, b, a = F(c), F(b), F(a)
    if c <= 0:
        return 0
    den = math.lcm(c.denominator, b.denominator, a.denominator) if hasattr(math, 'lcm') else c.denominator*b.denominator*a.denominator
    C, B, Q = int(c*den), int(b*den), int(a*den)
    safe = lambda t: C+B*t-Q*t*t > 0
    if Q == 0:
        return CAP if B >= 0 else min(CAP, (C-1)//(-B))
    assert Q > 0
    if safe(CAP):
        return CAP
    out = max(0, min(CAP, (B+math.isqrt(B*B+4*Q*C))//(2*Q)))
    while out and not safe(out):
        out -= 1
    while out < CAP and safe(out+1):
        out += 1
    assert safe(out) and not safe(out+1)
    return out


def expiry(state, query, target_radius, method):
    if state is None:
        return 0
    radius = target_radius+RADIUS
    if method == 'snapshot':
        squared = sum((max(F(lo), min(F(hi), F(q)))-q)**2 for (lo, hi, vl, vh), q in zip(state, query))
        distance_lower = math.isqrt(squared.numerator//squared.denominator)
        return prefix(distance_lower-radius, F(-5), F(0))
    assert method == 'history'
    directions = [tuple(n) for n in A.pose.DIRECTIONS[::15]]
    directions += [(-x, -y) for x, y in directions]
    # Also use the integer closest-point normal for current position box.
    closest = [max(F(lo), min(F(hi), F(q)))-q for (lo, hi, vl, vh), q in zip(state, query)]
    den = closest[0].denominator*closest[1].denominator
    adaptive = tuple(int(x*den) for x in closest)
    if any(adaptive):
        divisor = math.gcd(abs(adaptive[0]), abs(adaptive[1]))
        directions.append(tuple(x//divisor for x in adaptive))
    # Retain the strong isotropic proof using the valid history position box.
    best = expiry(state, query, target_radius, 'snapshot')
    for normal in directions:
        norm = root_up(sum(x*x for x in normal))
        p = sum(n*(F(lo if n >= 0 else hi)-q) for n, (lo, hi, vl, vh), q in zip(normal, state, query))
        v = sum(n*F(vl if n >= 0 else vh) for n, (lo, hi, vl, vh) in zip(normal, state))
        best = max(best, prefix(p-radius*norm, (v-150000*norm)/1000000, F(3*norm, 2000000)))
    return best


def own_position(own, basis):
    p = (np.asarray(own['center'])-basis['anchor'])@np.asarray(basis['road'])
    return [int(round(x*1000000)) for x in p[:2]]


def own_mask(xyz, transform, own, body):
    world = xyz@transform[:3, :3].T+transform[:3, 3]
    local = (world-own['location'])@np.asarray(own['matrix'])[:3, :3]
    inside = np.all(abs(local-body['offset']) <= np.asarray(body['extent'])+.03, axis=1)
    return xyz[~inside], int(inside.sum())


def encode(raw, transform, own, body, context, background, history, source_us, frame):
    xyz = np.c_[raw['x'], raw['y'], raw['z']].astype('<f4')
    kept, masked = own_mask(xyz, transform, own, body)
    bounds, geometry = A.center_bounds(kept, transform, context['extent'], context['basis'], background)
    history.append((source_us, bounds))
    history[:] = history[-7:]
    hist = extrema(history)
    snap = extrema(history[-1:])
    def fractions(s):
        return None if s is None else [[[x.numerator, x.denominator] for x in axis] for axis in s]
    obj = dict(version=1, context=hashlib.sha256(canonical(context)).hexdigest(), source_us=source_us,
               frame=frame, history=history, states=dict(history=fractions(hist), snapshot=fractions(snap)))
    data = canonical(obj)
    wire = zlib.compress(data+hashlib.sha256(data).digest(), 6)
    return wire, dict(bounds_um=bounds, geometry=geometry, masked_returns=masked)


def decode(wire, context):
    data = zlib.decompress(wire)
    assert len(data) > 32 and hashlib.sha256(data[:-32]).digest() == data[-32:]
    obj = json.loads(data[:-32])
    assert obj['version'] == 1 and obj['context'] == hashlib.sha256(canonical(context)).hexdigest()
    assert type(obj['source_us']) is int and obj['source_us'] >= 0
    for method, state in obj['states'].items():
        assert method in ('history', 'snapshot')
        if state is not None:
            assert len(state) == 2 and all(len(axis) == 4 for axis in state)
            obj['states'][method] = [[F(*value) for value in axis] for axis in state]
    return obj


def choose(cache, query, context, now, method):
    if cache is None:
        return dict(allowed=False, source_us=None, expiry_us=0)
    stamp = cache['source_us']
    age = expiry(cache['states'][method], query, A.pose.enclosing_radius_um(context['extent']), method)
    return dict(allowed=bool(stamp <= now and now+ACTION <= stamp+age), source_us=stamp,
                expiry_us=age, paid_age_us=now-stamp, action_end_us=now+ACTION)


def relay(own, go):
    speed = math.hypot(*own['velocity'][:2])
    if not go:
        return 0., 1.
    return (.8 if speed < .5 else 0.), (min(.4, max(0., .4*(speed-.5))) if speed > .55 else 0.)
