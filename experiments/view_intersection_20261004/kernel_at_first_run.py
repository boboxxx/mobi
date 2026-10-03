"""Receiver-only lens distance certificates, using integer support bounds.

Decimal finds candidates. Safety comes from exact integer primal/dual checks,
not from trusting a floating optimizer. Units are micrometers/microseconds.
"""
from decimal import Decimal, localcontext
from math import isqrt

POINT_SCALE = 10**12
NORM_SCALE = 10**6
WEIGHT_SCALE = 10**12
CAP = 500000

def ceilroot(n):
    k = isqrt(n)
    return k + (k*k < n)

def distance_point(p, q):
    n = sum((p[i]-q[i]*POINT_SCALE)**2 for i in range(2))
    lo = isqrt(n)//POINT_SCALE
    hi = (ceilroot(n)+POINT_SCALE-1)//POINT_SCALE
    return lo, hi

def feasible(p, center, radius):
    return sum((p[i]-center[i]*POINT_SCALE)**2 for i in range(2)) <= (radius*POINT_SCALE)**2

def dual_lower(p, a, b, q, radius, weights):
    # All ball members satisfy t.x <= t.center + radius*||t||.
    # Nonnegative combinations give a halfspace lower bound on distance.
    t = [[p[k]-c[k]*POINT_SCALE for k in range(2)] for c in (a,b)]
    u = [-sum(weights[i]*t[i][k] for i in range(2)) for k in range(2)]
    if not any(u):
        return 0
    numerator = sum(weights[i]*(sum(t[i][k]*(q[k]-c[k]) for k in range(2))*NORM_SCALE
                     - radius*ceilroot(sum(x*x for x in t[i])*NORM_SCALE**2))
                    for i,c in enumerate((a,b)))
    denominator = ceilroot(sum(x*x for x in u)*NORM_SCALE**2)
    return max(0, numerator//denominator)

def lens(a, b, q, radius):
    d2 = sum((a[k]-b[k])**2 for k in range(2))
    if d2 > 4*radius*radius:
        return dict(kind='disjoint')
    qp = [v*POINT_SCALE for v in q]
    if feasible(qp,a,radius) and feasible(qp,b,radius):
        return dict(kind='inside', point=qp, lower_um=0, upper_um=0)
    if d2 == 4*radius*radius:
        p = [(a[k]+b[k])*POINT_SCALE//2 for k in range(2)]
        lo,hi = distance_point(p,q)
        return dict(kind='tangent',point=p,lower_um=lo,upper_um=hi)
    with localcontext() as ctx:
        ctx.prec = 80
        da,db,dq = [[Decimal(v) for v in x] for x in (a,b,q)]
        rr = Decimal(radius)
        candidates = []
        for i,(c,other) in enumerate(((da,db),(db,da))):
            norm = sum((dq[k]-c[k])**2 for k in range(2)).sqrt()
            if norm:
                p = [c[k]+rr*(dq[k]-c[k])/norm for k in range(2)]
                if sum((p[k]-other[k])**2 for k in range(2)) <= rr*rr:
                    candidates.append((p,[Decimal(1 if j==i else 0) for j in range(2)]))
        mid = [(da[k]+db[k])/2 for k in range(2)]
        if d2:
            dist = Decimal(d2).sqrt()
            height = (rr*rr-Decimal(d2)/4).sqrt()
            perp = [-(db[1]-da[1])/dist,(db[0]-da[0])/dist]
            for sign in (-1,1):
                p = [mid[k]+sign*height*perp[k] for k in range(2)]
                t0,t1 = [[p[k]-c[k] for k in range(2)] for c in (da,db)]
                v = [dq[k]-p[k] for k in range(2)]
                determinant = t0[0]*t1[1]-t0[1]*t1[0]
                if determinant:
                    w = [(v[0]*t1[1]-v[1]*t1[0])/determinant,
                         (t0[0]*v[1]-t0[1]*v[0])/determinant]
                    # A wrong-sign candidate may still supply an upper bound;
                    # its exact dual remains safe but will fail the gap gate.
                    candidates.append((p,[max(Decimal(0),x) for x in w]))
        assert candidates
        chosen,weights = min(candidates,key=lambda item:sum((item[0][k]-dq[k])**2 for k in range(2)))
        maximum = max(weights)
        w = [int((x/maximum*WEIGHT_SCALE).to_integral_value()) if maximum else 0 for x in weights]
        # Move inward by the smallest tested amount, then verify feasibility
        # with integers. The midpoint is always feasible for equal-radius balls.
        for power in range(-12,1):
            epsilon = Decimal(10)**power
            p = [int(((1-epsilon)*chosen[k]+epsilon*mid[k])*POINT_SCALE) for k in range(2)]
            if feasible(p,a,radius) and feasible(p,b,radius):
                break
        else:
            raise AssertionError('No rational feasible witness')
        lo = dual_lower(p,a,b,q,radius,w)
        hi = distance_point(p,q)[1]
        assert lo <= hi
        return dict(kind='dual',point=p,weights=w,lower_um=lo,upper_um=hi)

def intersection_distance(left, right, q, radius):
    proofs=[]
    for i,a in enumerate(left):
        for j,b in enumerate(right):
            c = lens(a,b,q,radius)
            c.update(i=i,j=j)
            if c['kind']=='inside':
                return dict(status='bounded',lower_um=0,upper_um=0,proofs=[c])
            proofs.append(c)
    valid = [c for c in proofs if c['kind']!='disjoint']
    if not valid:
        return dict(status='empty',proofs=proofs)
    low = min(c['lower_um'] for c in valid)
    high = min(c['upper_um'] for c in valid)
    return dict(status='bounded' if high-low<=2 else 'precision_gap',
                lower_um=low,upper_um=high,proofs=proofs)

def horizon(distance, body_and_query):
    if distance <= body_and_query:
        return 0
    def safe(t):
        return 2000000*(distance-body_and_query) > 10000000*t+3*t*t
    if safe(CAP):
        return CAP
    lo,hi = 0,CAP
    while hi-lo>1:
        m = (lo+hi)//2
        if safe(m):lo=m
        else:hi=m
    return lo

def geometry(left_cm,right_cm,radius,body_um):
    left = [[int(v)*10000 for v in c] for c in left_cm]
    right = [[int(v)*10000 for v in c] for c in right_cm]
    if not left or not right:
        return dict(status='missing_view',queries=[])
    queries=[]
    for q in ((-6000000,0),(6000000,0)):
        d = intersection_distance(left,right,q,radius)
        if d['status']!='bounded':
            return dict(status=d['status'],queries=queries,failed_query=dict(query=list(q),distance=d))
        lower = horizon(d['lower_um'],body_um+750000)
        upper = horizon(d['upper_um'],body_um+750000)
        assert upper-lower<=1
        queries.append(dict(query=list(q),distance=d,lower_us=lower,upper_us=upper))
    return dict(status='bounded',queries=queries)
