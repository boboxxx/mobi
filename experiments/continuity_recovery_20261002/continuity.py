"""Typed, bounded backfill of a fixed class-center exclusion invariant.

An anchor is created only after a complete legacy receiver acceptance. Old
authority still expires. Historical steps prove continuous non-entry, never
infer empty interior from a new negative detection list.
"""
import copy, hashlib, json, math, sys
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/incremental_validity_20261002'))
from patch import body
from projection_once import projections as shared_projections
from native_pack import select
from fast_path import Receiver as LegacyReceiver

MAX_STEPS = 32
MAX_BYTES = 2_100_000


@dataclass(frozen=True)
class Anchor:
    identity: str
    scope: object
    motion: object
    reference_us: int
    endpoint_us: int
    sequence: int


def fixed(motion):
    return all(x == 0 for x in [motion.vx, motion.vy, motion.acceleration, motion.yaw_rate])


def registered_anchor(legacy_receiver, blob, scope, motion):
    """Use a receiver-owned FULL accepted proof, not an arbitrary Region claim."""
    identity = hashlib.sha256(blob).hexdigest()
    if (not isinstance(legacy_receiver, LegacyReceiver) or not fixed(motion)
            or identity not in legacy_receiver._history):
        raise ValueError('Missing accepted fixed-region anchor')
    raw, _, _ = body.decode(body.canonical(json.loads(blob)['raw']), legacy_receiver.profiles,
                            scope, legacy_receiver.contract)
    if (body.canonical(json.loads(blob)['motion']) != body.canonical(body.asdict(motion))
            or legacy_receiver._deadlines[identity] != raw['reference_us'] + raw['horizon_us']):
        raise ValueError('Anchor metadata mismatch')
    # The public helper receives an actual legacy Receiver; _history is a local
    # trusted store. No wire-supplied object can populate this store.
    region = legacy_receiver._history[identity]
    if region.center != tuple(scope.query) or region.episode != scope.episode or region.yaw != motion.yaw:
        raise ValueError('Anchor region mismatch')
    return Anchor(identity, scope, motion, raw['reference_us'],
                  raw['reference_us'] + raw['horizon_us'], raw['sequence'])


def reference_speed(profile, rays, reference_us):
    # Common class-speed bound at each selected observation timestamp.
    age = (reference_us - np.max(rays[:, 4])) / body.TIME_SCALE
    if age < 0:
        raise ValueError('Future observation')
    return replace(profile, speed=profile.speed + profile.acceleration * age)


def collar(profile, anchor, horizon, rays, reference_us):
    if not fixed(anchor.motion):
        raise ValueError('Only a fixed invariant is supported')
    cells = body.required(reference_speed(profile, rays, reference_us), anchor.motion, horizon)
    if cells is None:
        return None
    low, high, margin = body.envelope(anchor.motion, 0., profile.clock)
    q = profile.step / math.sqrt(2)
    # Only ENTIRE tiles inside the proved center-free K can be removed.
    inside = body.box_distance(cells, low, high) + q < margin + profile.r_max - 1e-9
    return cells[~inside]


def supports(result, profile, motion, cells, choose=False):
    if cells is None:
        return False, []
    missing = np.ones(len(cells), dtype=bool)
    w = result['witnesses'] @ body.rotation(motion.yaw)
    selected = []
    for error in np.unique(result['error']):
        radius = profile.r_min - error - profile.step / math.sqrt(2) - 1e-9
        todo = np.flatnonzero(missing)
        if radius <= 0 or not len(todo):
            continue
        group = np.flatnonzero(result['error'] == error)
        d, j = cKDTree(w[group]).query(cells[todo], k=1)
        hit = d < radius
        missing[todo[hit]] = False
        if choose:
            selected.extend(result['ray_indices'][group[j[hit]]].tolist())
    return not missing.any(), selected


def step(points, origin, observed, reference, profiles, contract, anchor,
         horizon, sequence, strategy='greedy', full=False):
    if (strategy not in ['nearest', 'greedy'] or not fixed(anchor.motion)
            or type(sequence) is not int or sequence < 0
            or not math.isfinite(horizon) or horizon <= 0
            or len({p.clock for p in profiles.values()}) != 1):
        raise ValueError('Invalid strategy or moving invariant')
    o, r, ref = body.encode_source(points, origin, observed, reference)
    result = shared_projections(o, r, ref, profiles, anchor.scope, contract)
    cells = {n: (body.required(reference_speed(p, r, ref), anchor.motion, horizon) if full
                 else collar(p, anchor, horizon, r, ref)) for n, p in profiles.items()}
    candidates = set()
    for n, p in profiles.items():
        ok, ids = supports(result[n], p, anchor.motion, cells[n], True)
        if not ok:
            return None
        candidates.update(ids)
    candidates = np.asarray(sorted(candidates), dtype=np.int64)
    chosen = candidates
    if strategy == 'greedy' and len(candidates):
        row_parts, col_parts, offset = [], [], 0
        for n, p in profiles.items():
            c = cells[n]
            if not len(c):
                continue
            v = result[n];use = np.isin(v['ray_indices'], candidates)
            ids = v['ray_indices'][use]
            w = v['witnesses'][use] @ body.rotation(anchor.motion.yaw)
            radii = p.r_min - v['error'][use] - p.step / math.sqrt(2) - 1e-9
            use = radii > 0;ids, w, radii = ids[use], w[use], radii[use]
            found = cKDTree(c).query_ball_point(w, radii)
            lengths = np.fromiter((len(x) for x in found), dtype=np.int64, count=len(found))
            if lengths.sum():
                cc = np.concatenate(found).astype(np.int64, copy=False)
                rr = np.repeat(np.arange(len(w)), lengths)
                strict = np.linalg.norm(c[cc] - w[rr], axis=1) < radii[rr]
                row_parts.append(np.searchsorted(candidates, ids[rr[strict]]))
                col_parts.append(offset + cc[strict])
            offset += len(c)
        rows, cols = np.concatenate(row_parts), np.concatenate(col_parts)
        order = np.lexsort((cols, rows));rows, cols = rows[order], cols[order]
        indptr = np.concatenate(([0], np.cumsum(np.bincount(rows, minlength=len(candidates)))))
        chosen = candidates[select(indptr, cols, np.arange(len(candidates)), offset, 1)]
    # Retain the observation supplying the common reference-speed bound even
    # when it was not chosen as a planar geometric support witness.
    chosen = np.unique(np.append(chosen, int(np.argmax(r[:, 4]))))
    if not len(chosen) or len(chosen) > body.MAX_RAYS:
        return None
    return json.loads(body.serialize(o, r[chosen], ref, profiles, anchor.scope,
                                     contract, horizon, sequence))


def wire(anchor, steps):
    if not 1 <= len(steps) <= MAX_STEPS or any(x is None for x in steps):
        return None
    blob = body.canonical(dict(kind='center-continuity-v1', dynamics='observation-speed-age-v1',
                               anchor=anchor.identity, steps=steps))
    return blob if len(blob) <= MAX_BYTES else None


class Receiver:
    def __init__(self, profiles, contract):
        self.profiles = profiles;self.contract = contract;self._anchors = {}
        self._last_reference = -1;self._last_sequence = -1;self.last = None
        self._verified_regions = {}

    def register(self, legacy_receiver, blob, scope, motion):
        if self.profiles != legacy_receiver.profiles or self.contract != legacy_receiver.contract:
            raise ValueError('Anchor physical-contract mismatch')
        anchor = registered_anchor(legacy_receiver, blob, scope, motion)
        packet = json.loads(blob)
        p, o, r = body.decode(body.canonical(packet['raw']), self.profiles, scope, self.contract)
        parent = self._verified_regions.get(packet['prior']) if packet['prior'] else None
        if packet['prior'] and parent is None:
            raise ValueError('Missing revalidated legacy parent')
        results = body.projections(o, r, p['reference_us'], self.profiles, scope, self.contract)
        for n, profile in self.profiles.items():
            c = body.required(reference_speed(profile, r, p['reference_us']), motion,
                              p['horizon_us'] / body.TIME_SCALE)
            if c is None:
                raise ValueError('Anchor outside finite domain')
            c = c[~body.prior_covers(c, scope, motion, parent, profile,
                                    p['reference_us'] / body.TIME_SCALE)]
            if not supports(results[n], profile, motion, c)[0]:
                raise ValueError('Anchor fails age/future revalidation')
        low, high, margin = body.envelope(motion, p['horizon_us'] / body.TIME_SCALE,
                                          max(v.clock for v in self.profiles.values()))
        self._verified_regions[anchor.identity] = body.Region(tuple(scope.query), motion.yaw,
            tuple(low), tuple(high), margin, anchor.reference_us / body.TIME_SCALE,
            anchor.endpoint_us / body.TIME_SCALE, anchor.identity, scope.episode)
        self._anchors[anchor.identity] = anchor
        self._last_reference = max(self._last_reference, anchor.reference_us)
        self._last_sequence = max(self._last_sequence, anchor.sequence)
        return anchor

    def inspect(self, blob):
        """Recompute historical facts; no receipt/action authority conferred."""
        if not isinstance(blob, bytes) or len(blob) > MAX_BYTES:
            raise ValueError('Invalid bounded bundle')
        b = json.loads(blob)
        if (set(b) != {'kind', 'dynamics', 'anchor', 'steps'}
                or b['kind'] != 'center-continuity-v1' or b['dynamics'] != 'observation-speed-age-v1'):
            raise ValueError('Wrong typed packet')
        anchor = self._anchors[b['anchor']]
        if not isinstance(b['steps'], list) or not 1 <= len(b['steps']) <= MAX_STEPS:
            raise ValueError('Invalid step count')
        end, previous, sequence = anchor.endpoint_us, anchor.reference_us, anchor.sequence
        for raw in b['steps']:
            p, o, r = body.decode(body.canonical(raw), self.profiles, anchor.scope, self.contract)
            ref, seq, h = p['reference_us'], p['sequence'], p['horizon_us']
            if not previous < ref < end or seq <= sequence or ref + h <= end:
                raise ValueError('Temporal gap, replay or nonextending evidence')
            projections = body.projections(o, r, ref, self.profiles, anchor.scope, self.contract)
            for n, profile in self.profiles.items():
                if not supports(projections[n], profile, anchor.motion,
                                collar(profile, anchor, h / body.TIME_SCALE, r, ref))[0]:
                    raise ValueError('Unexcluded reachability collar')
            end, previous, sequence = ref + h, ref, seq
        return dict(reference_us=previous, endpoint_us=end, sequence=sequence,
                    steps=len(b['steps']), anchor=anchor.identity)

    def accept(self, blob, now, execution=0.):
        try:
            if not math.isfinite(now) or not math.isfinite(execution) or execution < 0:
                return False
            decision = self.inspect(blob)
            received = math.ceil(Fraction.from_float(float(now)) * body.TIME_SCALE)
            action = math.ceil(Fraction.from_float(float(execution)) * body.TIME_SCALE)
            if (received < decision['reference_us'] or received + action >= decision['endpoint_us']
                    or decision['reference_us'] <= self._last_reference
                    or decision['sequence'] <= self._last_sequence):
                return False
            self.last = decision;self._last_reference = decision['reference_us']
            self._last_sequence = decision['sequence']
            return True
        except (ValueError, TypeError, KeyError, OverflowError, IndexError):
            return False
