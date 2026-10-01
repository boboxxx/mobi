"""Small exact reference and simple renewal baselines; no novelty claim."""
from functools import lru_cache


def advance(ages, ttl, action, success, service=1):
    nxt = [min(a + service, t + 1) for a, t in zip(ages, ttl)]
    if action is not None and success:
        nxt[action] = min(service, ttl[action] + 1)
    return tuple(nxt)


def valid(ages, ttl, required, guard):
    return all(ages[r] + guard <= ttl[r] for r in required)


@lru_cache(maxsize=500000)
def solve(ages, ttl, required, guard, service, horizon, p):
    if horizon == 0:
        return 0., 0., None
    best = None
    for action in (None,) + required:
        reward = cost = 0.
        for prob, success in ([(1., False)] if action is None else [(p, True), (1-p, False)]):
            if prob == 0:
                continue
            nxt = advance(ages, ttl, action, success, service)
            future = solve(nxt, ttl, required, guard, service, horizon-1, p)
            reward += prob * (valid(nxt, ttl, required, guard) + future[0])
            cost += prob * ((action is not None) + future[1])
        key = (round(reward, 12), -round(cost, 12), -(action if action is not None else -1))
        if best is None or key > best[0]:
            best = key, (reward, cost, action)
    return best[1]


def choose(method, ages, ttl, required, guard=1, service=1, p=.9, step=0):
    if not required:
        return None
    if method == 'edf':
        return min(required, key=lambda r: (ttl[r]-ages[r]-guard, r))
    if method == 'normalized_age':
        return max(required, key=lambda r: (ages[r]/max(1, ttl[r]-guard), -r))
    if method == 'long_first_cycle':
        return sorted(required, key=lambda r: (-ttl[r], r))[step % len(required)]
    if method == 'group_refresh':
        missing = [r for r in required if ages[r]+service+guard > ttl[r]]
        return max(missing, key=lambda r: (ttl[r], -r)) if missing else None
    if method in ('deterministic_mpc3', 'stochastic_mpc3', 'stochastic_mpc6'):
        depth = 6 if method == 'stochastic_mpc6' else 3
        probability = 1. if method == 'deterministic_mpc3' else p
        return solve(tuple(ages), tuple(ttl), tuple(required), guard, service, depth, probability)[2]
    raise ValueError(method)
