"""Independent-episode statistical bounds, NOT physical hard certificates."""
import math
import numpy as np
from scipy.stats import beta

SCALES=np.array([.1,.1,.1,.1])
FLOOR=np.array([0.,0.,0.,.05])


def features(record,kind):
    f=record['features'];v=f['speed']
    if kind=='constant':return np.array([1.])
    if kind!='state':raise ValueError('Unknown predictor')
    return np.array([1.,v,v*v,f['last_acceleration'],f['gear_is_1'],f['planned_throttle'],f['planned_brake'],f['target']])


def targets(record):
    future=[r for r in record['rows'] if r['phase'] in ['command','backup']];assert len(future)==41
    b=record['body'];ref=record['reference'];c=math.cos(math.radians(ref['yaw']));s=math.sin(math.radians(ref['yaw']));rotation=np.array([[c,-s],[s,c]])
    points=[]
    for r in [ref]+future:
        world=np.asarray(r['body_vertices'],dtype=float);assert world.shape==(8,3) and np.isfinite(world).all()
        points.extend((world[:,:2]-np.array([ref['x'],ref['y']]))@rotation)
    points=np.asarray(points);front=max(0.,float(points[:,0].max())-2.);rear=max(0.,-2.-float(points[:,0].min()));lateral=max(0.,float(np.abs(points[:,1]).max())-1.)
    stable=next((i for i in range(len(future)-4) if all(r['speed']<=.02 for r in future[i:])),None)
    duration=math.inf if stable is None else (stable+1)*.05
    if record['collisions']:duration=math.inf
    return np.array([front,rear,lateral,duration])


def fit(records,kind):
    y=np.array([targets(r) for r in records]);x=np.array([features(r,kind) for r in records])
    if not np.isfinite(y).all():return None
    return np.linalg.lstsq(x,y,rcond=None)[0]


def predict(record,kind,weights):
    if weights is None:return np.full(4,np.inf)
    return np.maximum(FLOOR,features(record,kind)@weights)


def score(observed,predicted):
    if not np.isfinite(observed).all() or not np.isfinite(predicted).all():return math.inf
    return max(0.,float(np.max((observed-predicted)/SCALES)))


def calibrate(records,kind,weights):
    if not records:raise ValueError('Empty calibration set')
    return max(score(targets(r),predict(r,kind,weights)) for r in records)


def upper_failure(failures,n,confidence=.95):
    if not 0<=failures<=n or n<0:raise ValueError('Invalid count')
    if not n:return None
    return 1. if failures==n else float(beta.ppf(confidence,failures+1,n-failures))


def max_score_confidence(n,alpha=.01):
    if n<=0 or not 0<alpha<1:raise ValueError('Invalid tolerance parameters')
    return -math.expm1(n*math.log1p(-alpha))
