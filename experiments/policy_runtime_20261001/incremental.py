"""Current-ray cell checks with cached witness INDEX hints, never cached truth.

Every cell is certified with current position and current reconstructed error.
Failed hints fall back to the complete reference query. Cached arrays cannot
grant a prior/free-space premise and do not establish physical contracts.
"""
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path
from dataclasses import asdict
import json,math,sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'policy_evidence_20261001'))
import policy_proof as pp


class Verifier:
    def __init__(self,max_cache=64):
        if type(max_cache) is not int or max_cache<=0:raise ValueError('Invalid cache bound')
        self.cache=OrderedDict();self.max_cache=max_cache
        self.counts=dict(cells=0,hint_hits=0,fallback_cells=0)

    def covered(self,result,profile,policy,speed,yaw,horizon):
        cells=pp.required(profile,policy,speed,horizon)
        if cells is None:return False
        key=(profile,policy,speed,horizon)
        w=result['witnesses']@pp.rotation(yaw);error=result['error']
        owners=self.cache.pop(key,None)
        if owners is None or len(owners)!=len(cells):owners=np.full(len(cells),-1,dtype=np.int64)
        else:owners=owners.copy()
        missing=np.ones(len(cells),dtype=bool)
        eligible=np.flatnonzero((owners>=0)&(owners<len(w)))
        if len(eligible):
            ray=owners[eligible]
            distance=np.linalg.norm(cells[eligible]-w[ray],axis=1)
            radius=profile.r_min-error[ray]-profile.step/math.sqrt(2)-1e-9
            hit=distance+1e-12<radius;missing[eligible[hit]]=False
        self.counts['cells']+=len(cells);self.counts['hint_hits']+=int((~missing).sum());self.counts['fallback_cells']+=int(missing.sum())
        owners[missing]=-1
        for e in np.unique(error):
            radius=profile.r_min-e-profile.step/math.sqrt(2)-1e-9
            if radius<=0:continue
            todo=np.flatnonzero(missing)
            if not len(todo):break
            group=np.flatnonzero(error==e)
            distance,j=cKDTree(w[group]).query(cells[todo],k=1)
            hit=distance<radius;indices=todo[hit]
            missing[indices]=False;owners[indices]=group[j[hit]]
        self.cache[key]=owners
        while len(self.cache)>self.max_cache:self.cache.popitem(last=False)
        return not missing.any()

    def verify(self,blob,profiles,scope,contract,policy,speed,yaw,now,min_sequence=0):
        try:
            if len(blob)>2_100_000 or not math.isfinite(now) or len({p.clock for p in profiles.values()})!=1:return False
            packet=json.loads(blob)
            if set(packet)!={'kind','policy','speed','yaw','raw'} or packet['kind']!='policy-evidence-v1':return False
            if type(packet['speed']) not in (float,int) or type(packet['yaw']) not in (float,int):return False
            if pp.canonical(packet['policy'])!=pp.canonical(asdict(policy)) or packet['speed']!=speed or packet['yaw']!=yaw:return False
            p,o,r=pp.decode(pp.canonical(packet['raw']),profiles,scope,contract)
            exact_now=Fraction.from_float(float(now))*pp.TIME_SCALE;receipt=math.ceil(exact_now)
            if p['sequence']<min_sequence or exact_now<p['reference_us'] or receipt>=p['reference_us']+p['horizon_us']:return False
            res=pp.projections(o,r,p['reference_us'],profiles,scope,contract)
            return all(self.covered(res[name],pr,policy,speed,yaw,p['horizon_us']/pp.TIME_SCALE) for name,pr in profiles.items())
        except (ValueError,TypeError,KeyError,OverflowError,IndexError):return False


def timing_after_verified(blob,policy,speed,now):
    """Only timing, callable after this same packet passed current verification.

    No second geometric verification is hidden outside the measured pipeline.
    This helper is not an independent admission or physical authorization API.
    """
    try:
        p=json.loads(blob)['raw']['payload'];receipt=math.ceil(Fraction.from_float(float(now))*pp.TIME_SCALE)
        if Fraction.from_float(float(now))*pp.TIME_SCALE<p['reference_us']:return False
        duration=pp.stop_duration(speed,(receipt-p['reference_us'])/pp.TIME_SCALE,policy)
        ticks=math.ceil(Fraction.from_float(float(duration))*pp.TIME_SCALE)
        return receipt+ticks<p['reference_us']+p['horizon_us']
    except (ValueError,TypeError,KeyError,OverflowError):return False
