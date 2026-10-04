"""Exact circle/pose pruning and conservative distance to their intersection."""
import math,sys
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/pose_support_20261004'))
from observer import DIRECTIONS,parameters,projections,boxes,horizon,score,geometry as pose_geometry
ETA_UM=10000
QUERIES=((-6000000,0),(6000000,0))
def upfraction(f):return (f.numerator+f.denominator-1)//f.denominator
def truth_integer(xy):
    fs=[F.from_float(float(v))*1000000 for v in xy];D=max(f.denominator for f in fs)
    return [f.numerator*(D//f.denominator) for f in fs],D
def error_um(center,xy):
    p,D=truth_integer(xy);n=sum((p[j]-center[j]*D)**2 for j in (0,1));r=math.isqrt(n);r+=r*r<n;return (r+D-1)//D
def conformity(hulls,extent,pred,xy,family):
    if not hulls:return F(0)
    p,D=truth_integer(xy);s=F(score(projections(hulls),extent,p,D),ETA_UM)
    if pred['status']!='supported':return s
    if family=='local_mean':e=error_um(pred['mean_um'],xy);scale=pred['single_scale_um']
    else:e=min(error_um(c,xy) for c in pred['centers_um']);scale=pred['modes_scale_um']
    return max(s,F(e,scale))
def rect_distance(rect,q):
    c,s=DIRECTIONS[rect['cell']];u=c*q[0]+s*q[1];v=-s*q[0]+c*q[1];a,b,z,w=rect['bounds'];du=max(a-u,0,u-b);dv=max(z-v,0,v-w)
    return du*du+dv*dv,rect['norm_sq']
def minrect(rects,q):
    vals=[rect_distance(r,q) for r in rects];n,d=min(vals,key=lambda v:F(v[0],v[1]));return math.isqrt(n//d)
def circle_distance(center,radius,q):return max(0,math.isqrt(sum((center[j]-q[j])**2 for j in (0,1)))-radius)
def infer(hulls,extent,pred,q,family,variant='clip'):
    q=F(q);delta=upfraction(q*ETA_UM);param=parameters(extent,delta)
    if not hulls:return dict(status='refused',lower_us=[],active_pairs=0,pruned_pairs=0)
    if pred['status']=='supported' and variant=='plain':
        centers=[pred['mean_um']] if family=='local_mean' else pred['centers_um'];scale=pred['single_scale_um'] if family=='local_mean' else pred['modes_scale_um'];radius=upfraction(q*scale)
        return dict(status='bounded',lower_us=[horizon(min(circle_distance(c,radius,query) for c in centers),param['body_um']) for query in QUERIES],active_pairs=0,pruned_pairs=0,radius_um=radius,fallback=False)
    rects=boxes(projections(hulls),param)
    if not rects:return dict(status='empty',lower_us=[],active_pairs=0,pruned_pairs=0)
    if pred['status']!='supported':
        g=pose_geometry(projections(hulls),param);return dict(status=g['status'],lower_us=[v['lower_us'] for v in g['queries']],active_pairs=0,pruned_pairs=0,fallback=True)
    centers=[pred['mean_um']] if family=='local_mean' else pred['centers_um'];scale=pred['single_scale_um'] if family=='local_mean' else pred['modes_scale_um'];radius=upfraction(q*scale);alive=[];pruned=0
    if variant=='clip':
        for center in centers:
            keep=[]
            for r in rects:
                n,d=rect_distance(r,center)
                if n>radius*radius*d:pruned+=1
                else:keep.append(r)
            if keep:alive.append((center,keep))
    if variant=='clip' and not alive:return dict(status='empty',lower_us=[],active_pairs=0,pruned_pairs=pruned,radius_um=radius)
    out=[]
    for query in QUERIES:
        if variant=='plain':lower=min(circle_distance(c,radius,query) for c in centers)
        elif variant=='max':lower=max(minrect(rects,query),min(circle_distance(c,radius,query) for c in centers))
        else:lower=min(max(circle_distance(c,radius,query),minrect(kept,query)) for c,kept in alive)
        out.append(horizon(lower,param['body_um']))
    return dict(status='bounded',lower_us=out,active_pairs=sum(len(v) for _,v in alive),pruned_pairs=pruned,radius_um=radius,fallback=False)
