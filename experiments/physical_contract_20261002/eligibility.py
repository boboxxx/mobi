"""Separate conditional mathematical lifetime from physical action eligibility.

The trusted population is configured locally, never inferred from detected actors.
Finite non-refutation cannot create a calibrated contract. This package has no
positive physical calibration certificate, hence grants no physical authority.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
MODEL=dict(center='actor_bounding_box_center',probe_plane='fixed_road_reference_plus_0.6m',classes=dict(small=dict(r_min=.2,r_max=.4),vehicle=dict(r_min=.55,r_max=2.5)),point_error=.01,origin_error=.01,query_error=.01,speed_at_observation=5.,acceleration=3.,clock=.02)
MODEL_ID=hashlib.sha256(canonical(MODEL)).hexdigest()
@dataclass(frozen=True)
class Assessment:
    conditional_horizon_us:int
    physical_status:str
    reasons:tuple
    model_id:str
    population:tuple
    def permits_physical_action(self):return False

class ContractGate:
    def __init__(self,analysis_path,audit_path,pinned_audit_sha256,allowed_population):
        blob=Path(audit_path).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=pinned_audit_sha256:raise ValueError('Untrusted audit bytes')
        data=Path(analysis_path).read_bytes();audit=json.loads(blob);analysis=json.loads(data)
        if hashlib.sha256(data).hexdigest()!=audit['analysis_sha256']:raise ValueError('Audit/analysis binding')
        population=tuple(sorted(set(allowed_population)))
        if not population or any(not isinstance(x,str) or not x for x in population):raise ValueError('Explicit nonempty allowed population required')
        indexed={x['id']:x for x in analysis['rows']};self.refuted={};self.sampled=set();self.population=population
        for x in audit['rows']:
            r=indexed[x['id']];bp=r['blueprint'];self.sampled.add(bp);reasons=[]
            if x['robust_exclusion']:reasons.append('opaque_core_refuted_at_declared_center')
            if x['actual_outer_failure']:reasons.append('outer_radius_refuted_at_declared_center')
            if x['any_center_outer_impossible']:reasons.append('outer_radius_refuted_for_every_center')
            if reasons:self.refuted.setdefault(bp,set()).update(reasons)
    def assess(self,conditional_horizon_us,model_id=MODEL_ID):
        if type(conditional_horizon_us) is not int or conditional_horizon_us<0:raise ValueError('Conditional horizon')
        reasons=[]
        if model_id!=MODEL_ID:status='unverified';reasons.append('changed_model_requires_new_validation')
        else:
            status='unverified'
            for bp in self.population:
                if bp in self.refuted:status='refuted';reasons.extend(bp+':'+x for x in sorted(self.refuted[bp]))
                elif bp in self.sampled:reasons.append(bp+':finite_nonrefutation_is_not_calibration')
                else:reasons.append(bp+':outside_audited_population')
        return Assessment(conditional_horizon_us,status,tuple(reasons),model_id,self.population)

class OperationalBoundary:
    """Wrap a conditional receiver; preserve its diagnostic clock and horizon.

    Every known physical premise still needs independent calibration/structural
    evidence. This negative-evidence registry can deny eligibility, not certify it.
    The wrapper is a misuse boundary, not a new useful-driving controller.
    """
    def __init__(self,conditional_receiver,gate):self.receiver=conditional_receiver;self.gate=gate
    def assess(self):
        endpoint,_=self.receiver.authority
        return self.gate.assess(max(0,endpoint-self.receiver.ref))
    def can_act(self,now_us,reserve_us=200000):
        return self.assess().permits_physical_action() and self.receiver.can_act(now_us,reserve_us)
