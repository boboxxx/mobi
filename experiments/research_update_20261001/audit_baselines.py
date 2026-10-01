#!/usr/bin/env python3
"""Finite baseline audit; frozen September core is imported, never edited.

The simple baseline knows channel identifiers and contention mode, exactly like
set_joint. It does not evaluate set utility or a joint probability. A matching
result shows the old gain is insufficient evidence for a new semantic algorithm.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/carla_v2x_full'))
import core

ORIGINAL = core.select_messages
SCENARIOS = ('free', 'hazard_a', 'hazard_b', 'both_hazard', 'permanent_block')
METHODS = ('coverage_greedy', 'set_joint', 'channel_greedy')


def channel_greedy(evidence, cycle, config):
    missing = core.unresolved_regions(evidence, cycle, config['ttl'])
    if not missing:
        missing = sorted(core.REGIONS, key=lambda r: evidence[r][1])[:max(1, config['slots'])]
    candidates = sorted((p for p in core.PROVIDERS if p.region in missing),
                        key=lambda p: (core.marginal_success(p, config), p.name), reverse=True)
    chosen = []
    for p in candidates:
        if len(chosen) == config['slots']:
            break
        if any(p.region == q.region for q in chosen):
            continue
        if config['mode'] == 'contention' and any(p.channel == q.channel for q in chosen):
            continue
        chosen.append(p)
    # Canonical order prevents spurious differences from the legacy sequential RNG.
    return [p.name for p in core.PROVIDERS if p in chosen]


def select(method, evidence, cycle, config):
    if method == 'channel_greedy':
        return channel_greedy(evidence, cycle, config)
    return ORIGINAL(method, evidence, cycle, config)


def state_audit():
    rows = []
    for name, config in core.CONFIGS.items():
        mismatches = 0
        count = 0
        # Covers absent, expired, fresh and tied/unequal ages and both contents.
        items = [None] + [(value, age, 'audit') for value in ('free', 'occupied')
                          for age in range(0, 8)]
        for a, b in itertools.product(items, repeat=2):
            evidence = {r: value for r, value in zip(core.REGIONS, (a, b)) if value is not None}
            lhs = ORIGINAL('set_joint', evidence, 8, config)
            rhs = channel_greedy(evidence, 8, config)
            count += 1
            mismatches += lhs != rhs
        rows.append(dict(config=name, states=count, selection_mismatches=mismatches))
    return rows


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=200)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    rows = []
    core.select_messages = select
    try:
        for config in core.CONFIGS:
            for scenario in SCENARIOS:
                for seed in range(args.seeds):
                    # Reuse seed ID across scenarios; cluster by seed in aggregation.
                    for method in METHODS:
                        row = core.run_episode(method, config, scenario, seed)
                        rows.append(row)
    finally:
        core.select_messages = ORIGINAL
    write_csv(args.out / 'per_episode.csv', rows)
    comparisons = []
    rng = np.random.default_rng(20261001)
    for config in core.CONFIGS:
        lookup = {(r['method'], r['scenario'], r['seed']): r for r in rows if r['config'] == config}
        for baseline in ('channel_greedy', 'coverage_greedy'):
            values = [np.mean([lookup['set_joint', s, seed]['progress_fraction'] -
                               lookup[baseline, s, seed]['progress_fraction']
                               for s in SCENARIOS if s != 'permanent_block']) for seed in range(args.seeds)]
            x = np.asarray(values)
            boot = x[rng.integers(0, len(x), (4000, len(x)))].mean(axis=1)
            exact = all(lookup['set_joint', s, seed][metric] == lookup[baseline, s, seed][metric]
                        for s in SCENARIOS for seed in range(args.seeds)
                        for metric in ('progress_fraction', 'unsafe_go_fraction', 'bytes_sent', 'selection_signature'))
            comparisons.append(dict(config=config, method='set_joint', baseline=baseline,
                                    seed_clusters=len(x), progress_diff=float(x.mean()),
                                    ci_low=float(np.quantile(boot, .025)), ci_high=float(np.quantile(boot, .975)),
                                    all_checked_episode_metrics_identical=exact))
    write_csv(args.out / 'paired_comparisons.csv', comparisons)
    states = state_audit()
    write_csv(args.out / 'state_audit.csv', states)
    manifest = dict(seeds=args.seeds, episodes=len(rows), elapsed_s=time.perf_counter()-start,
                    date='2026-10-01', methods=METHODS, configs=list(core.CONFIGS), scenarios=SCENARIOS,
                    core_sha256=hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest(),
                    audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    noise=dict(false_free=.01, false_occupied=.03),
                    rng='Legacy sequential stream retained for attribution; equal actions consume identical draws. No common exogenous trace claimed for differing actions.',
                    interpretation='Equality disproves uniqueness of the earlier mechanism evidence, not utility in all future settings.')
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(manifest=manifest, comparisons=comparisons, state_audit=states), indent=2))


if __name__ == '__main__':
    main()
