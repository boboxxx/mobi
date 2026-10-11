"""Post-result lossless computation change, not a changed physical rollout.

The original expiry is max(radial, directional proofs), capped at CAP.
Reaching CAP is an exact stopping condition; later proofs cannot improve it.
"""
import math
from fractions import Fraction as F
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'experiments/closed_loop_motion_20261011'))
import runtime as R


def expiry(state, query, target_radius, method):
    if state is None or method == 'snapshot':
        return R.expiry(state, query, target_radius, method)
    assert method == 'history'
    best = R.expiry(state, query, target_radius, 'snapshot')
    if best == R.CAP:
        return best
    radius = target_radius+R.RADIUS
    directions = [tuple(n) for n in R.A.pose.DIRECTIONS[::15]]
    directions += [(-x, -y) for x, y in directions]
    closest = [max(F(lo), min(F(hi), F(q)))-q for (lo, hi, vl, vh), q in zip(state, query)]
    den = closest[0].denominator*closest[1].denominator
    adaptive = tuple(int(x*den) for x in closest)
    if any(adaptive):
        divisor = math.gcd(abs(adaptive[0]), abs(adaptive[1]))
        directions.append(tuple(x//divisor for x in adaptive))
    for normal in directions:
        norm = R.root_up(sum(x*x for x in normal))
        p = sum(n*(F(lo if n >= 0 else hi)-q) for n, (lo, hi, vl, vh), q in zip(normal, state, query))
        v = sum(n*F(vl if n >= 0 else vh) for n, (lo, hi, vl, vh) in zip(normal, state))
        best = max(best, R.prefix(p-radius*norm, (v-150000*norm)/1000000, F(3*norm, 2000000)))
        if best == R.CAP:
            break
    return best
