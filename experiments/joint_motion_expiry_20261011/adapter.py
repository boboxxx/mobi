"""Frozen XYZ geometry to outward center AABBs; no actor labels or truth."""
import importlib.util
from fractions import Fraction as F
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


front = module('joint_xyz_frontend', 'experiments/body_expiry_20261004/frontend.py')
pose = module('joint_pose_geometry', 'experiments/pose_support_20261004/observer.py')


def center_bounds(xyz, transform, extent, basis, background):
    groups = front.groups(xyz, transform, np.asarray(basis['anchor']),
                          np.asarray(basis['road']), extent,
                          background['layouts']['0']['codes'])
    parameters = pose.parameters(extent)
    rects = pose.boxes(pose.projections(groups), parameters) if groups else []
    if not rects:
        return None, dict(groups=len(groups), cells=0)
    limits = [[None, None], [None, None]]
    for rect in rects:
        c, s = pose.DIRECTIONS[rect['cell']]
        ulo, uhi, vlo, vhi = rect['bounds']
        den = rect['norm_sq']
        for u in (ulo, uhi):
            for v in (vlo, vhi):
                for axis, num in enumerate((c*u-s*v, s*u+c*v)):
                    x = F(num, den)
                    limits[axis][0] = x if limits[axis][0] is None else min(limits[axis][0], x)
                    limits[axis][1] = x if limits[axis][1] is None else max(limits[axis][1], x)
    bounds = [[lo.numerator//lo.denominator,
               -((-hi.numerator)//hi.denominator)] for lo, hi in limits]
    return bounds, dict(groups=len(groups), cells=len(rects))
