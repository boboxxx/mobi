"""Current XYZ to complete retained component point sets; no labels or truth inputs."""
import math
import numpy as np

def groups(xyz,T,anchor,road,extent,static):
 local=(np.asarray(xyz,dtype=float)@T[:3,:3].T+T[:3,3]-anchor)@road
 selected=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*extent[2]+.3)
 g=np.floor(local*10).astype(np.int64);code=(g[:,0]+120)*161*27+(g[:,1]+80)*27+g[:,2]-3
 selected&=~((local[:,2]<3)&np.isin(code,static));p=local[selected]
 if not len(p):return []
 cells={}
 for i,key in enumerate(map(tuple,np.floor(p[:,:2]/.2).astype(int))):cells.setdefault(key,[]).append(i)
 remaining=set(cells);out=[]
 while remaining:
  seed=min(remaining);remaining.remove(seed);stack=[seed];ids=[]
  while stack:
   key=stack.pop();ids.extend(cells[key])
   for dx in (-1,0,1):
    for dy in (-1,0,1):
     other=(key[0]+dx,key[1]+dy)
     if other in remaining:remaining.remove(other);stack.append(other)
  pp=p[ids];lo=pp.min(0);hi=pp.max(0)
  if len(pp)>=3 and max(hi[:2]-lo[:2])<=2*math.sqrt(sum(x*x for x in extent))+.2 and hi[2]-lo[2]<=2*extent[2]+.2:out.append(np.unique(np.rint(pp[:,:2]*100).astype(np.int32),axis=0).tolist())
 return out
