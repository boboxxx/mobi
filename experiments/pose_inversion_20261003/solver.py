"""Query-directed, conservative continuous-pose inversion of a fixed score."""
import collections,heapq,math,sys,time
from fractions import Fraction
from pathlib import Path
import numpy as np
from bounds import Cell,RayIndex,rotation,value
PREVIOUS=Path(__file__).resolve().parents[1]/'shape_evidence_20261002'
sys.path.insert(0,str(PREVIOUS))
from model import score,fraction
from lifetime import State,expiry

CAP_US=500000
SPEED=5000000
ACCELERATION=3000000
QUERY_RADIUS=750000

def age_bounds(dx_um,dy_um,radius_um):
    r=expiry([State(int(dx_um),int(dy_um),int(radius_um),SPEED,ACCELERATION)],(0,0),QUERY_RADIUS,CAP_US,True)
    upper=0 if r['reason'] is not None else CAP_US if r['capped'] else r['safe_through_us']+1
    return r['safe_through_us'],upper

def cell_age(cell,query,radius_um):
    # Round distance toward zero; this only enlarges the possible collision set.
    d=np.maximum(np.maximum(np.asarray(cell.lo[:2])-query,query-np.asarray(cell.hi[:2])),0)
    return age_bounds(*np.floor(d*1e6-1e-7).clip(0).astype(np.int64),radius_um)[0]

def prior(extent):
    return Cell((-12.,-8.,float(extent[2]-.1),math.radians(-2),0.,math.radians(-2)),(12.,8.,float(extent[2]+.1),math.radians(2),2*math.pi,math.radians(2)))

def solve(indexes,extent,anchor,road_rotation,query,threshold,max_nodes=2000,policy='priority'):
    if policy not in ('priority','fifo'):raise ValueError('Policy')
    if not indexes or max_nodes<1 or not 0<=threshold<=1:raise ValueError('Solver input')
    start=time.perf_counter();root=prior(extent);query=np.asarray(query,dtype=float);radius_um=math.ceil(float(np.linalg.norm(extent))*1e6)
    # Boundary-and-beyond is always unknown. No artificial free domain boundary.
    distances=[query[0]+12,12-query[0],query[1]+8,8-query[1]];edge=int(np.argmin(distances));outside_distance=max(0,min(distances));outside_lower=age_bounds(max(0,math.floor(outside_distance*1e6-1e-7)),0,radius_um)[0];outside_upper=age_bounds(math.ceil(outside_distance*1e6+1e-7),0,radius_um)[1]
    upper=outside_upper;witness=dict(kind='unknown_boundary',edge=edge,distance_m=outside_distance,upper_us=upper);nodes=[];heap=[];fifo=collections.deque();examined=0;cache={};scored_points=0
    def add(cell,parent):
        i=len(nodes);lo=cell_age(cell,query,radius_um);nodes.append(dict(id=i,parent=parent,lo=list(cell.lo),hi=list(cell.hi),lower_us=lo,status='pending'));heapq.heappush(heap,(lo,i));fifo.append(i)
    def probe(cell):
        nonlocal upper,witness,scored_points
        p=cell.center();p[:2]=np.clip(query,cell.lo[:2],cell.hi[:2]);p[:3]=np.round(p[:3]*1e6)/1e6
        if np.any(p<cell.lo) or np.any(p>cell.hi):p=cell.center()
        key=tuple(p)
        if key not in cache:
            center=np.asarray(anchor)+road_rotation@p[:3];rot=rotation(*p[3:]);scores=[]
            for idx in indexes:
                ss=score(idx.points,idx.origin,center,rot,extent);scored_points+=len(idx.points);scores.append(ss)
                if fraction(ss)>threshold:break
            cache[key]=scores
        scores=cache[key]
        if len(scores)==len(indexes) and all(fraction(s)<=threshold for s in scores):
            delta=(p[:2]-query)*1e6
            # Pose is an exact retained model witness; conservatively round its
            # distance upward for a collision-time upper bound.
            du=int(math.ceil(float(np.linalg.norm(delta))+1e-7));_,u=age_bounds(du,0,radius_um)
            if u<upper:upper=u;witness=dict(kind='retained_pose',pose=p.tolist(),scores=scores,upper_us=u,distance_upper_um=du)
    add(root,None)
    while (heap if policy=='priority' else fifo) and examined<max_nodes and upper>0:
        i=heapq.heappop(heap)[1] if policy=='priority' else fifo.popleft();node=nodes[i];cell=Cell(tuple(node['lo']),tuple(node['hi']));examined+=1
        if node['lower_us']>=upper-1:node['status']='time_retained';continue
        bounds=[]
        for idx in indexes:
            b=idx.bound(cell,extent,anchor,road_rotation);bounds.append(b)
            if value(b)>threshold:break
        node['bounds']=bounds
        if any(value(b)>threshold for b in bounds):node['status']='excluded';continue
        probe(cell)
        if upper==0:node['status']='witness_retained';break
        if examined==max_nodes:node['status']='budget_retained';break
        a,b=cell.split(extent);node['status']='split';node['children']=[len(nodes),len(nodes)+1];add(a,i);add(b,i)
    retained=[x for x in nodes if x['status'] not in ('excluded','split')];lower=min([outside_lower]+[x['lower_us'] for x in retained]);assert lower<=upper
    return dict(lower_us=lower,upper_us=upper,gap_us=upper-lower,cap_us=CAP_US,query_xy=query.tolist(),query_radius_um=QUERY_RADIUS,body_radius_um=radius_um,speed_um_s=SPEED,acceleration_um_s2=ACCELERATION,threshold=dict(numerator=threshold.numerator,denominator=threshold.denominator),policy=policy,max_nodes=max_nodes,examined_nodes=examined,excluded_leaves=sum(x['status']=='excluded' for x in nodes),retained_leaves=len(retained),exact_pose_probes=len(cache),exact_probe_point_checks=scored_points,outside_lower_us=outside_lower,witness=witness,nodes=nodes,elapsed_s=time.perf_counter()-start)
