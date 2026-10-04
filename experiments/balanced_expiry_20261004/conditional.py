"""Exact fixed-selector binary episode-risk tests; not a new statistical theorem."""
import math
from fractions import Fraction as F


def cdf(k, n, probability):
    probability = F(probability)
    assert isinstance(n, int) and isinstance(k, int) and 0 <= k <= n and 0 <= probability <= 1
    return sum(F(math.comb(n, j)) * probability ** j * (1-probability) ** (n-j)
               for j in range(k+1))


def upper(k, n, delta):
    delta = F(delta)
    assert 0 < delta < 1 and 0 <= k <= n
    if not n or k == n:
        return F(1)
    lo, hi = F(0), F(1)
    for _ in range(64):
        mid = (lo + hi) / 2
        if cdf(k, n, mid) > delta:
            lo = mid
        else:
            hi = mid
    return hi


def certificate(selected, failed, *, risk=F(1,20), delta=F(1,20), policies=1):
    selected, failed = list(selected), list(failed)
    assert len(selected) == len(failed) and policies >= 1
    assert all(type(v) is bool for v in selected + failed)
    assert all(not f or s for s, f in zip(selected, failed))
    n = sum(selected)
    k = sum(failed)
    bound = upper(k, n, F(delta)/policies)
    p = cdf(k, n, risk) if n else F(1)
    accepted = bool(n and p <= F(delta)/policies)
    if accepted:
        # The exact test additionally proves the endpoint <= target, even when
        # a rational boundary is not representable by the dyadic bisection grid.
        bound = min(bound, F(risk))
    return dict(planned_episodes=len(selected), authorized_episodes=n,
                failed_authorized_episodes=k, conditional_upper=[bound.numerator,bound.denominator],
                p_value=[p.numerator,p.denominator], risk_target=[F(risk).numerator,F(risk).denominator],
                family_count=policies, accepted=accepted,
                scope='Conditional on at least one authorization in an iid whole episode '
                      'for a policy fixed independently of these certification data. '
                      'Not per-query, per-location, unknown-actor or physical collision risk.')


def zero_failure_required(risk, delta, policies):
    risk, delta = F(risk), F(delta)
    assert 0 < risk < 1 and 0 < delta < 1 and policies >= 1
    n = 0
    while (1-risk)**n > delta/policies:
        n += 1
    return n
