"""Separate geometric fallback and supported errors; offline scores, label-free runtime."""
import sys
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/prospective_hypotheses_20261004'))
from scores import body_violation
from geometry import infer as learned_infer,conformity as learned_score
from observer import score,projections
from geometry import truth_integer
from inference import infer as joint_infer
FAMILIES=('component_mean','component_modes')
COMPONENTS=('supported_mean','supported_modes','fallback_um')

def conformity(hulls,extent,prediction,xy):
    out=dict(supported_mean=F(0),supported_modes=F(0),fallback_um=F(0))
    if not hulls:return out
    if prediction['status']=='supported':
        for mode in ('mean','modes'):
            out['supported_'+mode]=learned_score(hulls,extent,prediction,xy,'local_'+mode)
    else:
        p,denominator=truth_integer(xy)
        out['fallback_um']=F(max(score(projections(hulls),extent,p,denominator),body_violation(hulls,extent,xy)))
    return out

def infer(hulls,extent,prediction,thresholds,family):
    assert family in FAMILIES
    assert F(thresholds['supported'])>=0
    delta=thresholds['fallback_um'];assert isinstance(delta,int) and delta>=0
    if not hulls:return dict(status='refused',lower_us=[],kind='empty_observation')
    if prediction['status']!='supported':
        result=joint_infer(hulls,extent,{},F(delta),'joint')
        return dict(status=result['status'],lower_us=result['lower_us'],kind='fallback_joint',delta_um=delta,joint_geometry=result)
    result=learned_infer(hulls,extent,prediction,F(thresholds['supported']),'local_'+family[len('component_'):],'max')
    return dict(status=result['status'],lower_us=result['lower_us'],kind='supported_intersection',geometry=result)

def simultaneous_error_bound(n,classes=6):
    """Three component events/class: two supported, one shared fallback, each 2.5%."""
    assert isinstance(n,int) and n>0
    return 3*classes*F(39,40)**n
