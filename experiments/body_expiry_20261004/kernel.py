"""Exact primal/dual certificates for complete same-radius ball intersections."""
import ctypes,math
from functools import reduce
from pathlib import Path
import numpy as np
PS=10**6;NS=10**6;WS=10**12;CAP=500000
_LIB=None

def lib():
 global _LIB
 if _LIB is None:
  _LIB=ctypes.CDLL(str(Path(__file__).resolve().parent/'proposer.so'));i64p=ctypes.POINTER(ctypes.c_int64);ip=ctypes.POINTER(ctypes.c_int)
  _LIB.hull.argtypes=[i64p,ctypes.c_int,i64p];_LIB.hull.restype=ctypes.c_int
  _LIB.propose.argtypes=[i64p,ctypes.c_int,ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,i64p,i64p,ip,i64p,ip];_LIB.propose.restype=ctypes.c_int
 return _LIB

def ptr(a):return a.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
def hull(points):
 a=np.ascontiguousarray(points,dtype=np.int64).reshape(-1,2);out=np.empty_like(a);n=lib().hull(ptr(a),len(a),ptr(out));return out[:n].tolist()
def ceilroot(n):
 k=math.isqrt(n);return k+(k*k<n)
def feasible(p,centers,r,den=PS):return all(sum((p[k]-c[k]*den)**2 for k in (0,1))<=(r*den)**2 for c in centers)
def point_distance(p,q,den=PS):
 n=sum((p[k]-q[k]*den)**2 for k in (0,1));return math.isqrt(n)//den,(ceilroot(n)+den-1)//den

def variance_certificate(centers,ids,r):
 ids=[int(i) for i in ids if i>=0];c=[centers[i] for i in ids]
 if len(ids)==1:w=[1]
 elif len(ids)==2:w=[1,1]
 else:
  a,b,z=c;u=[b[k]-a[k] for k in (0,1)];v=[z[k]-a[k] for k in (0,1)];det=u[0]*v[1]-u[1]*v[0]
  if det==0:return None
  uu=sum(x*x for x in u);vv=sum(x*x for x in v);num=[uu*v[1]-vv*u[1],u[0]*vv-v[0]*uu];den=2*det*det;w1=num[0]*v[1]-num[1]*v[0];w2=u[0]*num[1]-u[1]*num[0];w=[den-w1-w2,w1,w2]
 if min(w)<0 or not sum(w):return None
 divisor=reduce(math.gcd,w);w=[x//divisor for x in w];W=sum(w);s=[sum(w[i]*c[i][k] for i in range(len(w))) for k in (0,1)];gap=W*sum(w[i]*sum(x*x for x in c[i]) for i in range(len(w)))-sum(x*x for x in s)-W*W*r*r
 if gap<0:return None
 return dict(kind='empty' if gap>0 else 'singleton',indices=ids,weights=w,point_num=s,point_den=W,variance_gap=gap)

def dual_lower(p,centers,ids,weights,q,r):
 cc=[centers[i] for i in ids];t=[[p[k]-c[k]*PS for k in (0,1)] for c in cc];u=[-sum(weights[i]*t[i][k] for i in range(len(t))) for k in (0,1)]
 if not any(u):return 0
 N=sum(weights[i]*(sum(t[i][k]*(q[k]-c[k]) for k in (0,1))*NS-r*ceilroot(sum(x*x for x in t[i])*NS*NS)) for i,c in enumerate(cc));D=ceilroot(sum(x*x for x in u)*NS*NS);return max(0,N//D)

def intersection(centers,q,r):
 centers=[list(map(int,c)) for c in centers];q=list(map(int,q));qp=[x*PS for x in q]
 if not centers:return dict(kind='refused')
 if feasible(qp,centers,r):return dict(kind='inside',point=qp,lower_um=0,upper_um=0)
 # Exact two-ball/three-ball variance can prove emptiness or a singleton.
 a=np.ascontiguousarray(centers,dtype=np.int64);p=np.zeros(2,np.int64);anchor=np.zeros(2,np.int64);ids=np.full(2,-1,np.int32);weights=np.zeros(2,np.int64);mec=np.full(3,-1,np.int32)
 status=lib().propose(ptr(a),len(a),r,q[0],q[1],ptr(p),ptr(anchor),ids.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),ptr(weights),mec.ctypes.data_as(ctypes.POINTER(ctypes.c_int)))
 cert=variance_certificate(centers,mec,r)
 if cert:
  if cert['kind']=='singleton':
   if not feasible(cert['point_num'],centers,r,cert['point_den']):return dict(kind='precision_refusal',proposal_status=status)
   cert['lower_um'],cert['upper_um']=point_distance(cert['point_num'],q,cert['point_den'])
  return cert
 if status!=0:return dict(kind='precision_refusal',proposal_status=status)
 original=[int(v) for v in p];anchor=[int(v) for v in anchor];point=original if feasible(original,centers,r) else None
 for exponent in range(12,-1,-1):
  if point is not None:break
  D=10**exponent;candidate=[((D-1)*original[k]+anchor[k])//D for k in (0,1)]
  if feasible(candidate,centers,r):point=candidate;break
 if point is None:return dict(kind='precision_refusal',proposal_status=status)
 ii=[int(v) for v in ids if v>=0];ww=[int(weights[k]) for k,v in enumerate(ids) if v>=0];low=dual_lower(point,centers,ii,ww,q,r);high=point_distance(point,q)[1]
 if high-low>2:return dict(kind='precision_refusal',lower_um=low,upper_um=high,point=point,indices=ii,weights=ww)
 assert 0<=low<=high
 return dict(kind='dual',point=point,indices=ii,weights=ww,lower_um=low,upper_um=high)

def horizon(d,b):
 if d<=b:return 0
 def safe(t):return 2000000*(d-b)>10000000*t+3*t*t
 if safe(CAP):return CAP
 lo,hi=0,CAP
 while hi-lo>1:
  m=(lo+hi)//2
  if safe(m):lo=m
  else:hi=m
 return lo

def geometry(groups_cm,r,body):
 if not groups_cm:return dict(status='refused',queries=[])
 hh=[hull(g) for g in groups_cm];cc=[[[v*10000 for v in c] for c in h] for h in hh];queries=[]
 for q in ((-6000000,0),(6000000,0)):
  proofs=[intersection(g,q,r) for g in cc]
  if any(c['kind']=='precision_refusal' for c in proofs):return dict(status='precision_refusal',hulls_cm=hh,queries=queries,failed_query=dict(query=list(q),proofs=proofs))
  alive=[c for c in proofs if c['kind']!='empty']
  if not alive:return dict(status='empty',hulls_cm=hh,queries=queries,failed_query=dict(query=list(q),proofs=proofs))
  low=min(c['lower_um'] for c in alive);high=min(c['upper_um'] for c in alive);lower=horizon(low,body+750000);upper=horizon(high,body+750000)
  if upper-lower>1:return dict(status='precision_refusal',hulls_cm=hh,queries=queries,failed_query=dict(query=list(q),proofs=proofs))
  queries.append(dict(query=list(q),proofs=proofs,lower_um=low,upper_um=high,lower_us=lower,upper_us=upper))
 return dict(status='bounded',hulls_cm=hh,queries=queries)
