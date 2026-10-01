#!/usr/bin/env python3
"""Small exact oracle for renewable evidence; diagnostic, not a driving planner.

All reports are assumed correct and free. TTLs must be supplied by an external
conservative physical model. Successful reception alone does not certify safety.
An action must remain supported for `guard` slots after the commit instant.
"""
from functools import lru_cache


def advance(ages, ttl, action, success=True):
    # Ages are measured at commit; a sample produced now arrives one slot later.
    nxt = [min(a + 1, t + 1) for a, t in zip(ages, ttl)]
    if action is not None and success:
        nxt[action] = 1
    return tuple(nxt)


def sufficient(ages, ttl, required, guard=1):
    return all(ages[r] + guard <= ttl[r] for r in required)


def choose(method, ages, ttl, required, guard=1, horizon=3, success_p=.9):
    if not required:
        return None
    if method == 'max_age':
        return max(required, key=lambda r: (ages[r], -r))
    if method == 'edf':
        return min(required, key=lambda r: (ttl[r] - ages[r] - guard, r))
    if method in ('myopic_completion', 'finite_horizon'):
        depth = 1 if method == 'myopic_completion' else horizon
        return solve(tuple(ages), tuple(ttl), tuple(required), guard, depth, success_p)[2]
    raise ValueError(method)


@lru_cache(maxsize=150000)
def solve(ages, ttl, required, guard, horizon, success_p):
    if horizon == 0:
        return (0., 0., None)
    best = None
    for action in (None,) + required:
        reward = cost = 0.
        outcomes = [(1., False)] if action is None else [(success_p, True), (1-success_p, False)]
        for probability, success in outcomes:
            nxt = advance(ages, ttl, action, success)
            future = solve(nxt, ttl, required, guard, horizon-1, success_p)
            reward += probability * (int(sufficient(nxt, ttl, required, guard)) + future[0])
            cost += probability * ((action is not None) + future[1])
        # Exact finite-horizon objective, then fewer transmissions, stable tie.
        key = (round(reward, 12), -round(cost, 12), -(action if action is not None else -1))
        if best is None or key > best[0]:
            best = (key, (reward, cost, action))
    return best[1]
