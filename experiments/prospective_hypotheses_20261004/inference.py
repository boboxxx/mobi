"""Frozen-model state inputs and exact registered-actor age functions."""
import sys
from fractions import Fraction as F
from pathlib import Path
from scores import ROOT,local_predict,ridge_predict
from geometry import infer as local_infer
from integer_state import circle_age,body_um
sys.path.insert(0,str(ROOT/'experiments/body_expiry_20261004'))
from kernel import geometry as sphere_geometry
from frontend import groups
from observer import parameters,projections,geometry as pose_geometry
PRIMARY=('joint','ridge','local_mean','local_modes')
DIAGNOSTICS=('local_mean_plain','local_modes_plain','local_modes_clip')
def state(hulls,layout,bp,models,family):
    local,ridge,prepared=models
    if family=='joint':return {}
    if family=='ridge':return dict(center_um=ridge_predict(hulls,layout,ridge[bp]['ridge']))
    full=local_predict(hulls,layout,local[bp],prepared[bp]);out=dict(status=full['status'])
    if full['status']=='supported':
        if family=='local_mean':out.update(mean_um=full['mean_um'],single_scale_um=full['single_scale_um'])
        else:out.update(centers_um=full['centers_um'],modes_scale_um=full['modes_scale_um'])
    return out
def infer(hulls,extent,hypothesis,q,family,variant='max'):
    q=F(q)
    if family=='ridge':
        if not hulls:return dict(status='refused',lower_us=[])
        assert q.denominator==1
        return dict(status='bounded',lower_us=[circle_age(hypothesis['center_um'],int(q),body_um(extent),query) for query in ((-6000000,0),(6000000,0))])
    if family!='joint':return local_infer(hulls,extent,hypothesis,q,family,variant)
    assert q.denominator==1
    param=parameters(extent,int(q));s=sphere_geometry(hulls,param['body_um']+8000+int(q),param['body_um']);p=pose_geometry(projections(hulls),param)
    if 'empty' in (s['status'],p['status']):status='empty';ages=[]
    else:
        bounded=[g for g in (s,p) if g['status']=='bounded'];status='bounded' if bounded else 'refused';ages=[max(g['queries'][i]['lower_us'] for g in bounded) for i in (0,1)] if bounded else []
    return dict(status=status,lower_us=ages,sphere=s,pose=p)
def compact(out):return dict(status=out['status'],lower_us=out['lower_us'])
