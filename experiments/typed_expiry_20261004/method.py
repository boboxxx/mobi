"""Preserve supported constraint units; isolate fallback scaling, one event; no truth in runtime inference."""
import sys
from pathlib import Path
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/prospective_hypotheses_20261004'))
from scores import error, body_violation
from geometry import truth_integer, upfraction, circle_distance, minrect
from observer import score, projections, parameters, boxes, horizon
from inference import infer as baseline_infer
from integer_state import body_um

FAMILIES = ('typed_mean', 'typed_modes')
QUERIES = ((-6000000, 0), (6000000, 0))


def unit(extent, prediction, family):
    assert family in FAMILIES
    if prediction['status'] == 'supported':
        field = 'single_scale_um' if family == 'typed_mean' else 'modes_scale_um'
        value = prediction[field]
        assert isinstance(value, int) and value >= 50000
        return 10000, value
    value = max(50000, body_um(extent))
    return value, value


def conformity(hulls, extent, prediction, xy, family):
    """Offline label API: supported pose+circle, fallback body+pose."""
    if not hulls:
        return F(0)
    p, denominator = truth_integer(xy)
    pose = score(projections(hulls), extent, p, denominator)
    if prediction['status'] == 'supported':
        centers = ([prediction['mean_um']] if family == 'typed_mean'
                   else prediction['centers_um'])
        residual = min(error(c, xy) for c in centers)
    else:
        residual = body_violation(hulls, extent, xy)
    pose_unit, circle_unit = unit(extent, prediction, family)
    return max(F(pose, pose_unit), F(residual, circle_unit))


def infer(hulls, extent, prediction, threshold, family):
    """Known class/extent, observed hulls, frozen prediction and threshold only."""
    assert family in FAMILIES and F(threshold) >= 0
    if not hulls:
        return dict(status='refused', lower_us=[], kind='empty_observation')
    pose_unit, circle_unit = unit(extent, prediction, family)
    delta = upfraction(F(threshold) * pose_unit)
    radius = upfraction(F(threshold) * circle_unit)
    if prediction['status'] != 'supported':
        result = baseline_infer(hulls, extent, {}, F(delta), 'joint')
        return dict(status=result['status'], lower_us=result['lower_us'],
                    kind='fallback_joint', pose_unit_um=pose_unit, circle_unit_um=circle_unit, radius_um=radius, delta_um=delta,
                    joint_geometry=result)
    rects = boxes(projections(hulls), parameters(extent, delta))
    if not rects:
        return dict(status='empty', lower_us=[], kind='supported_intersection',
                    pose_unit_um=pose_unit, circle_unit_um=circle_unit, radius_um=radius, delta_um=delta)
    centers = ([prediction['mean_um']] if family == 'typed_mean'
               else prediction['centers_um'])
    distances = [max(minrect(rects, q),
                     min(circle_distance(c, radius, q) for c in centers))
                 for q in QUERIES]
    return dict(status='bounded', lower_us=[horizon(d, body_um(extent)) for d in distances],
                kind='supported_intersection', pose_unit_um=pose_unit, circle_unit_um=circle_unit, radius_um=radius, delta_um=delta)
