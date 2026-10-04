"""Frozen four-family current-center scores; labels only in this offline API."""
import hashlib,json,math,sys
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/calibrated_hypotheses_20261004'))
from model import predict as local_predict,prepare
from geometry import conformity,truth_integer
from observer import score,projections,enclosing_radius_um
from predictor import predict as ridge_predict
FAMILIES=('joint','ridge','local_mean','local_modes')
def load_models():
    local=json.loads((ROOT/'results/calibrated_hypotheses_20261004/models_sheng.json').read_bytes())['models'];ridge=json.loads((ROOT/'results/state_predictor_20261004/models_sheng.json').read_bytes())['models']
    return local,ridge,{bp:prepare(m) for bp,m in local.items()}
def predictions(hulls,layout,bp,models):
    local,ridge,prepared=models
    return local_predict(hulls,layout,local[bp],prepared[bp]),ridge_predict(hulls,layout,ridge[bp]['ridge'])
def error(center,xy):
    p,D=truth_integer(xy);n=sum((p[j]-center[j]*D)**2 for j in (0,1));r=math.isqrt(n);r+=r*r<n;return (r+D-1)//D
def body_violation(hulls,extent,xy):
    p,D=truth_integer(xy);base=enclosing_radius_um(extent)+8000;values=[]
    for h in hulls:
        values.append(max(0,max(error([v*10000 for v in pt],xy) for pt in h)-base))
    return min(values) if values else 0
def current_scores(hulls,extent,pred,centre,xy):
    if not hulls:return {m:F(0) for m in FAMILIES}
    p,D=truth_integer(xy);joint=max(score(projections(hulls),extent,p,D),body_violation(hulls,extent,xy))
    return dict(joint=F(joint),ridge=F(error(centre,xy)),local_mean=conformity(hulls,extent,pred,xy,'local_mean'),local_modes=conformity(hulls,extent,pred,xy,'local_modes'))
