"""Exact outward center-error radii and strict source-age bounds, in um/us."""
import math

def truth_integer(xy):
    pairs=[float(x).as_integer_ratio() for x in xy];D=max(p[1] for p in pairs)
    return [p[0]*(D//p[1])*1000000 for p in pairs],D
def ceilroot(n):
    r=math.isqrt(n);return r+(r*r<n)
def error_um(center,xy):
    num,D=truth_integer(xy);s=sum((center[j]*D-num[j])**2 for j in (0,1));v=ceilroot(s)
    return (v+D-1)//D
def body_um(ext):
    # Circumscribes all bbox yaw/tilt orientations: 3D radius outward integer.
    ratios=[float(x).as_integer_ratio() for x in ext];D=max(p[1] for p in ratios);s=sum((p[0]*(D//p[1])*1000000)**2 for p in ratios)
    return (ceilroot(s)+D-1)//D
def age(clearance):
    if clearance<=0:return 0
    lo=0;hi=500001
    while hi-lo>1:
        t=(lo+hi)//2
        if 2*5000000*t*1000000+3000000*t*t < 2*clearance*1000000000000:lo=t
        else:hi=t
    return lo
def circle_age(center,radius,body,query):
    dist=math.isqrt(sum((center[j]-query[j])**2 for j in (0,1)))
    return age(max(0,dist-radius)-body-750000)
def oracle_age(xy,body,query):
    num,D=truth_integer(xy);dist=math.isqrt(sum((num[j]-query[j]*D)**2 for j in (0,1)))//D
    return age(dist-body-750000)
