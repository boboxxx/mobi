"""XYZ-only positive-evidence center sets; no semantic or actor labels."""
import math
import numpy as np

GRID=.2
MIN_POINTS=3

def centers(points,anchor,road,extent):
    points=np.asarray(points,dtype=float)
    local=(points-np.asarray(anchor))@np.asarray(road)
    ext=np.asarray(extent)
    selected=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3)
    p=local[selected]
    if not len(p):return np.empty((0,2)),dict(selected=0,components=0,retained=0)
    grid=np.floor(p[:,:2]/GRID).astype(np.int64)
    cells={}
    for i,key in enumerate(map(tuple,grid)):cells.setdefault(key,[]).append(i)
    remaining=set(cells);groups=[]
    while remaining:
        seed=min(remaining);remaining.remove(seed);stack=[seed];ids=[]
        while stack:
            key=stack.pop();ids.extend(cells[key])
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    other=(key[0]+dx,key[1]+dy)
                    if other in remaining:remaining.remove(other);stack.append(other)
        groups.append(np.array(ids,dtype=int))
    result=[];maxspan=2*np.linalg.norm(ext)+.2
    for ids in groups:
        pp=p[ids];lo=pp.min(axis=0);hi=pp.max(axis=0)
        if len(ids)>=MIN_POINTS and max(hi[0]-lo[0],hi[1]-lo[1])<=maxspan and hi[2]-lo[2]<=2*ext[2]+.2:
            result.append((lo[:2]+hi[:2])/2)
    return np.array(result,dtype=float).reshape(-1,2),dict(selected=len(p),components=len(groups),retained=len(result))

def quantized_centers(c):
    # Nearest1cm centers, plus8mm radius covers the two-axis rounding displacement.
    return np.rint(np.asarray(c)*100).astype(np.int32)

def score(c,true_xy):
    if not len(c):return 0. # Only valid when the declared entire episode refuses.
    return float(np.min(np.linalg.norm(np.asarray(c)-np.asarray(true_xy),axis=1)))

def radius_um(scores,alpha=.05):
    k=math.ceil((len(scores)+1)*(1-alpha))
    if k>len(scores):return None
    return math.ceil(sorted(scores)[k-1]*1e6+1e-7)+8000

