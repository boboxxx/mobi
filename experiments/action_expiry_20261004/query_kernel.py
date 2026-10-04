"""Conditional source-age proposals for arbitrary disk queries; no risk transfer."""
import importlib.util
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


pose = module('action_fixed_pose', 'experiments/pose_support_20261004/observer.py')
balls = module('action_fixed_balls', 'experiments/body_expiry_20261004/kernel.py')


def integer(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError('Invalid integer contract value')
    return value


def point(value):
    if len(value) != 2:
        raise ValueError('Expected a planar point')
    return tuple(integer(v, -10**9, 10**9) for v in value)


def ceil_fraction(value):
    return (value.numerator + value.denominator - 1) // value.denominator


def rect_squared(rect, query):
    c, s = pose.DIRECTIONS[rect['cell']]
    u, v = c * query[0] + s * query[1], -s * query[0] + c * query[1]
    a, b, z, w = rect['bounds']
    return max(a-u, 0, u-b)**2 + max(z-v, 0, v-w)**2, rect['norm_sq']


def rect_contains(rect, numerator, denominator):
    c, s = pose.DIRECTIONS[rect['cell']]
    u = c*numerator[0] + s*numerator[1]
    v = -s*numerator[0] + c*numerator[1]
    a, b, z, w = rect['bounds']
    return a*denominator <= u <= b*denominator and z*denominator <= v <= w*denominator


def project_rect(rect, numerator, denominator):
    c, s = pose.DIRECTIONS[rect['cell']]
    u, v = c*numerator[0] + s*numerator[1], -s*numerator[0] + c*numerator[1]
    a, b, z, w = rect['bounds']
    u = max(a*denominator, min(b*denominator, u))
    v = max(z*denominator, min(w*denominator, v))
    return (c*u-s*v, s*u+c*v), denominator*rect['norm_sq']


@dataclass(frozen=True)
class Motion:
    speed_um_s: int = 5000000
    acceleration_um_s2: int = 3000000
    cap_us: int = 500000

    def __post_init__(self):
        integer(self.speed_um_s, 0, 100000000)
        integer(self.acceleration_um_s2, 0, 100000000)
        integer(self.cap_us, 1, 500000)


def horizon(distance_um, body_um, query_radius_um, motion=Motion()):
    gap = distance_um-body_um-query_radius_um
    if gap <= 0:
        return 0
    def safe(t):
        return 2*10**12*gap > 2*10**6*motion.speed_um_s*t + motion.acceleration_um_s2*t*t
    lo, hi = 0, motion.cap_us
    if safe(hi):
        return hi
    while lo+1 < hi:
        mid = (lo+hi)//2
        if safe(mid):
            lo = mid
        else:
            hi = mid
    return lo


class Evidence:
    """Compile observable geometry once; query without changing source epoch.

    Geometry is conditional on center membership and body/motion assumptions.
    This class deliberately has no deployment-authorizing certificate: changing
    query selection/controller/service law cannot inherit the earlier certificate.
    """
    def __init__(self, hulls_cm, extent, hypothesis, thresholds, family, source_us):
        self.source_us = integer(source_us, 0, 10**15)
        if family not in ('component_mean', 'component_modes'):
            raise ValueError('Unknown family')
        if len(extent) != 3 or any(not math.isfinite(float(v)) or not 0 < v <= 10 for v in extent):
            raise ValueError('Invalid declared body extent')
        self.family = family
        self.body_um = pose.parameters(extent)['body_um']
        self.centers = ()
        self.ball_groups = ()
        self.witness = None
        self.status = 'refused_empty_observation'
        if not hulls_cm:
            return
        hulls = [tuple(point(tuple(integer(v, -100000, 100000)*10000 for v in p)) for p in h) for h in hulls_cm]
        if any(not h for h in hulls):
            raise ValueError('Empty hull component')
        self.supported = hypothesis.get('status') == 'supported'
        if self.supported:
            q = Fraction(thresholds['supported'])
            if q < 0:
                raise ValueError('Negative calibration threshold')
            delta = ceil_fraction(q*10000)
            scale = integer(hypothesis['single_scale_um'] if family == 'component_mean' else hypothesis['modes_scale_um'], 1, 10**8)
            self.radius_um = ceil_fraction(q*scale)
            raw_centers = [hypothesis['mean_um']] if family == 'component_mean' else hypothesis['centers_um']
            self.centers = tuple(point(c) for c in raw_centers)
            if not self.centers:
                raise ValueError('Missing hypothesis centers')
        else:
            delta = integer(thresholds['fallback_um'], 0, 10**8)
            self.radius_um = self.body_um+8000+delta
            self.ball_groups = tuple(hulls)
        self.rects = tuple(pose.boxes(pose.projections(hulls_cm), pose.parameters(extent, delta)))
        if not self.rects:
            self.status = 'refused_empty_pose_set'
            return
        if self.supported:
            # Exact nonemptiness of (union circles) intersect (union rectangles).
            alive = any(n <= self.radius_um**2*d for c in self.centers
                        for n, d in (rect_squared(r, c) for r in self.rects))
            self.status = 'bounded' if alive else 'refused_disjoint_supported_sets'
        else:
            self.witness = self._fallback_witness()
            self.status = 'bounded' if self.witness is not None else 'refused_joint_feasibility_unproved'

    def _fallback_witness(self):
        # Finite proposal search. Every returned rational point is checked exactly.
        # A failed search is a precision/refusal result, never a proof of emptiness.
        for centers in self.ball_groups:
            proposal = balls.intersection(centers, (0, 0), self.radius_um)
            if proposal['kind'] in ('empty', 'precision_refusal', 'refused'):
                continue
            if proposal['kind'] == 'singleton':
                numerator, denominator = proposal['point_num'], proposal['point_den']
            else:
                numerator, denominator = proposal['point'], balls.PS
            for rect in self.rects:
                candidate, den = project_rect(rect, numerator, denominator)
                if balls.feasible(candidate, centers, self.radius_um, den) and rect_contains(rect, candidate, den):
                    return dict(point_num=list(candidate), point_den=den)
            for rect in self.rects:
                candidate, den = project_rect(rect, numerator, denominator)
                query = tuple(v//den for v in candidate)
                proposal2 = balls.intersection(centers, query, self.radius_um)
                if proposal2['kind'] in ('empty', 'precision_refusal', 'refused'):
                    continue
                if proposal2['kind'] == 'singleton':
                    pp, dd = proposal2['point_num'], proposal2['point_den']
                else:
                    pp, dd = proposal2['point'], balls.PS
                if balls.feasible(pp, centers, self.radius_um, dd) and rect_contains(rect, pp, dd):
                    return dict(point_num=list(pp), point_den=dd)
        return None

    def query(self, center_um, radius_um=750000, motion=Motion()):
        query = point(center_um)
        radius_um = integer(radius_um, 0, 100000000)
        if not isinstance(motion, Motion):
            raise ValueError('Missing declared motion contract')
        base = dict(source_us=self.source_us, query_um=list(query), query_radius_um=radius_um,
                    family=self.family, status=self.status, deployment_authorized=False,
                    risk_certificate_applicable=False)
        if self.status != 'bounded':
            return dict(base, lower_us=0, proposal_valid_until_us=self.source_us)
        n, d = min((rect_squared(r, query) for r in self.rects), key=lambda v: Fraction(*v))
        pose_lower = math.isqrt(n//d)
        proofs = None
        if self.supported:
            other = min(max(0, math.isqrt(sum((c[k]-query[k])**2 for k in (0, 1)))-self.radius_um) for c in self.centers)
        else:
            proofs = [balls.intersection(c, query, self.radius_um) for c in self.ball_groups]
            if any(v['kind'] in ('precision_refusal', 'refused') for v in proofs):
                return dict(base, status='refused_distance_precision', lower_us=0, proposal_valid_until_us=self.source_us)
            alive = [v for v in proofs if v['kind'] != 'empty']
            if not alive:
                return dict(base, status='refused_empty_body_set', lower_us=0, proposal_valid_until_us=self.source_us)
            other = min(v['lower_um'] for v in alive)
        lower = max(pose_lower, other)
        age = horizon(lower, self.body_um, radius_um, motion)
        return dict(base, distance_lower_um=lower, lower_us=age, body_proofs=proofs,
                    proposal_valid_until_us=self.source_us+age,
                    assumptions='True center in compiled set; declared body and motion bounds. No transferred selective certificate.')


def decision(proposal, now_us, action_us):
    integer(now_us, 0, 10**15)
    integer(action_us, 1, 500000)
    eligible = (proposal['status'] == 'bounded' and proposal['source_us'] <= now_us
                and now_us+action_us <= proposal['proposal_valid_until_us'])
    return dict(geometry_eligible=eligible, deployment_authorized=False,
                reason='New query/controller/service policy requires its own independent certification',
                now_us=now_us, action_us=action_us, source_us=proposal['source_us'],
                proposal_valid_until_us=proposal['proposal_valid_until_us'])
