"""Exact finite Bayesian stress test, not a driving benchmark."""
import argparse
import hashlib
import itertools
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd


def values(priors, dependencies, rewards, fnr, fpr, q, alpha=0.03):
    n = len(priors)
    states = np.array(list(itertools.product([0, 1], repeat=n)))
    prior = np.prod(np.where(states, priors, 1-priors), axis=1)
    unsafe = (states @ dependencies.T) > 0
    output = np.zeros(1 << n)
    hazards = np.zeros(1 << n)
    progress = np.zeros(1 << n)
    for mask in range(1 << n):
        ids = [i for i in range(n) if mask >> i & 1]
        obs = np.array(list(itertools.product([0, 1, 2], repeat=len(ids))), dtype=int)
        joint = np.broadcast_to(prior[:, None], (len(states), len(obs))).copy()
        for k, i in enumerate(ids):
            positive = np.where(states[:, i], 1-fnr[i], fpr[i])
            likelihood = np.where(obs[:, k][None, :] == 2, 1-q,
                                  q*np.where(obs[:, k][None, :] == 1,
                                             positive[:, None], 1-positive[:, None]))
            joint *= likelihood
        mass = joint.sum(axis=0)
        posterior_risk = (joint.T @ unsafe) / np.maximum(mass[:, None], 1e-30)
        gain = rewards[None, :] - 20 * posterior_risk
        gain = np.where(posterior_risk <= alpha, gain, -1e6)
        action = gain.argmax(axis=1)  # action 0 is always safe stop, reward 0
        chosen_risk = posterior_risk[np.arange(len(obs)), action]
        progress[mask] = (mass * rewards[action]).sum()
        hazards[mask] = (mass * chosen_risk).sum()
        output[mask] = progress[mask] - 20*hazards[mask]
        assert abs(mass.sum()-1) < 1e-9
    return output, hazards, progress


def greedy(value, k, tie):
    chosen = 0
    for _ in range(k):
        ids = [i for i in range(len(tie)) if not chosen >> i & 1]
        if not ids:
            break
        i = max(ids, key=lambda j: (round(value[chosen | (1 << j)]-value[chosen], 12), tie[j], -j))
        chosen |= 1 << i
    return chosen


def pairwise(value, k, tie):
    chosen = 0
    while chosen.bit_count() < k:
        ids = [i for i in range(len(tie)) if not chosen >> i & 1]
        moves = [(i,) for i in ids]
        if k-chosen.bit_count() >= 2:
            moves += list(itertools.combinations(ids, 2))
        if not moves:
            break
        def score(move):
            new = chosen | sum(1 << i for i in move)
            return (round((value[new]-value[chosen])/len(move), 12),
                    sum(tie[i] for i in move)/len(move), -len(move))
        move = max(moves, key=score)
        chosen |= sum(1 << i for i in move)
    return chosen


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--seeds', type=int, default=20)
    p.add_argument('--cases-per-seed', type=int, default=10)
    args = p.parse_args()
    start = time.time()
    rows = []
    for seed in range(args.seeds):
        rng = np.random.default_rng(20260926+seed)
        for case in range(args.cases_per_seed):
            priors = rng.uniform(.04, .22, 4)
            fnr, fpr = rng.uniform(.02, .1, 4), rng.uniform(.01, .05, 4)
            tie = -priors*np.log(priors)-(1-priors)*np.log1p(-priors)
            for family in ['single_requirement', 'two_requirements', 'three_requirements']:
                degree = ['single_requirement', 'two_requirements', 'three_requirements'].index(family)+1
                deps = np.zeros((5, 4), dtype=int)
                for a in range(1, 5):
                    deps[a, rng.choice(4, degree, replace=False)] = 1
                rewards = np.r_[0, rng.uniform(.7, 1.0, 4)]
                for q in [1.0, .8, .5]:
                    val, haz, prog = values(priors, deps, rewards, fnr, fpr, q)
                    for k in [1, 2, 3, 4]:
                        exact = max((m for m in range(16) if m.bit_count() <= k),
                                    key=lambda m: (val[m], -m.bit_count(), -m))
                        entropy = sum(1 << int(i) for i in np.argsort(-tie)[:k])
                        choices = {'no_comm': 0, 'entropy': entropy,
                                   'greedy_voi': greedy(val, k, tie),
                                   'pair_lookahead': pairwise(val, k, tie),
                                   'exact_subset': exact}
                        for method, mask in choices.items():
                            rows.append(dict(seed=seed, case=case, family=family, q=q, budget=k,
                                             method=method, mask=mask, utility=val[mask],
                                             hazard=haz[mask], progress=prog[mask],
                                             optimality_gap=val[exact]-val[mask]))
        print(f'Bayes seed {seed+1}/{args.seeds} elapsed={time.time()-start:.1f}s', flush=True)
    out = Path(args.output);out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows);df.to_csv(out/'per_case.csv', index=False)
    df.groupby(['family','q','budget','method'])[['utility','hazard','progress','optimality_gap']].mean().to_csv(out/'summary.csv')
    paired = df.pivot_table(index=['seed','case','family','q','budget'], columns='method', values='utility').reset_index()
    paired['exact_gain'] = paired.exact_subset-paired.greedy_voi
    paired['pair_gain'] = paired.pair_lookahead-paired.greedy_voi
    paired.to_csv(out/'paired.csv', index=False)
    (out/'manifest.json').write_text(json.dumps(dict(host=platform.node(), arguments=vars(args),
        seconds=time.time()-start, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        description='Exact expected utility of generated Bayesian models; no traffic dataset, no closed loop.'), indent=2))


if __name__ == '__main__':
    main()
