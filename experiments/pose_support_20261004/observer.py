"""Complete unknown-yaw inverse boxes, with exact integer projection distances.
A fixed tilt prior is explicit. No truth/labels/estimated single yaw enter this API.
"""
import json,math
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent
DIRECTIONS=json.loads((E/'directions.json').read_bytes())['normal_xy']
DIRECTION_ARRAY=np.array(DIRECTIONS,dtype=np.int64)
QUANTIZATION_UM=8000
TILT_NUM=87267;YAW_CELL_NUM=8730;FACTOR_DEN=1000000
CAP=500000

def rootup(n):s=math.isqrt(n);return s+(s*s<n)
def exact_extent_um(v):
 num,den=float(v).as_integer_ratio();return (num*1000000+den-1)//den

def enclosing_radius_um(extent):
 ratios=[float(v).as_integer_ratio() for v in extent];D=max(t[1] for t in ratios);n=sum((v*(D//d)*1000000)**2 for v,d in ratios);return (rootup(n)+D-1)//D

def parameters(extent,slack=0):
 body=enclosing_radius_um(extent);xy=enclosing_radius_um(extent[:2]);tilt=(body*TILT_NUM+FACTOR_DEN-1)//FACTOR_DEN;cell=(xy*YAW_CELL_NUM+FACTOR_DEN-1)//FACTOR_DEN;pad=tilt+cell+QUANTIZATION_UM+int(slack);return dict(body_um=body,xy_um=xy,tilt_pad_um=tilt,yaw_cell_pad_um=cell,slack_um=int(slack),half_extent_um=[exact_extent_um(v)+pad for v in extent[:2]])

def projections(hulls_cm):
 out=[]
 for group in hulls_cm:
  p=np.asarray(group,dtype=np.int64)*10000;u=p@DIRECTION_ARRAY.T;v=p@np.c_[-DIRECTION_ARRAY[:,1],DIRECTION_ARRAY[:,0]].T
  out.append(np.c_[u.min(0),u.max(0),v.min(0),v.max(0)].tolist())
 return out

def boxes(projected,params):
 A,B=params['half_extent_um'];out=[]
 for gid,table in enumerate(projected):
  for i,(umin,umax,vmin,vmax) in enumerate(table):
   c,s=DIRECTIONS[i];nn=c*c+s*s;nu=rootup(nn);bounds=[umax-A*nu,umin+A*nu,vmax-B*nu,vmin+B*nu]
   if bounds[0]<=bounds[1] and bounds[2]<=bounds[3]:out.append(dict(group=gid,cell=i,bounds=bounds,norm_sq=nn))
 return out

def membership(projected,params,point_num,point_den=1):
 A,B=params['half_extent_um']
 for table in projected:
  for i,(umin,umax,vmin,vmax) in enumerate(table):
   c,s=DIRECTIONS[i];nu=rootup(c*c+s*s);u=c*point_num[0]+s*point_num[1];v=-s*point_num[0]+c*point_num[1]
   if (umax-A*nu)*point_den<=u<=(umin+A*nu)*point_den and (vmax-B*nu)*point_den<=v<=(vmin+B*nu)*point_den:return True
 return False

def score(projected,extent,point_num,point_den):
 if not projected:return 0
 params=parameters(extent);A,B=params['half_extent_um'];best=None
 for table in projected:
  for i,(umin,umax,vmin,vmax) in enumerate(table):
   c,s=DIRECTIONS[i];nu=rootup(c*c+s*s);u=c*point_num[0]+s*point_num[1];v=-s*point_num[0]+c*point_num[1];excess=max(0,(umax-A*nu)*point_den-u,u-(umin+A*nu)*point_den,(vmax-B*nu)*point_den-v,v-(vmin+B*nu)*point_den);delta=(excess+nu*point_den-1)//(nu*point_den)
   if best is None or delta<best:best=delta
 return best

def horizon(d,body):
 gap=d-body-750000
 if gap<=0:return 0
 safe=lambda t:2000000*gap>10000000*t+3*t*t
 if safe(CAP):return CAP
 lo,hi=0,CAP
 while lo+1<hi:
  m=(lo+hi)//2
  if safe(m):lo=m
  else:hi=m
 return lo

def distance(rects,q):
 best=None
 for rect in rects:
  c,s=DIRECTIONS[rect['cell']];u=c*q[0]+s*q[1];v=-s*q[0]+c*q[1];a,b,z,w=rect['bounds'];cu=max(a,min(b,u));cv=max(z,min(w,v));n=(cu-u)**2+(cv-v)**2;den=rect['norm_sq']
  if best is None or n*best['squared_den']<best['squared_num']*den:best=dict(**rect,squared_num=n,squared_den=den,closest_num_um=[c*cu-s*cv,s*cu+c*cv],closest_den=den)
 assert best;lo=math.isqrt(best['squared_num']//best['squared_den']);hi=lo+(lo*lo*best['squared_den']<best['squared_num']);return dict(**best,lower_um=lo,upper_um=hi)

def geometry(projected,params):
 if not projected:return dict(status='refused',queries=[],feasible_cells=0)
 rects=boxes(projected,params)
 if not rects:return dict(status='empty',queries=[],feasible_cells=0)
 queries=[]
 for q in ((-6000000,0),(6000000,0)):
  d=distance(rects,q);queries.append(dict(query=list(q),**d,lower_us=horizon(d['lower_um'],params['body_um']),upper_us=horizon(d['upper_um'],params['body_um'])))
 return dict(status='bounded',queries=queries,feasible_cells=len(rects))
