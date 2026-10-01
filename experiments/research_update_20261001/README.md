# Finite literature-driven audit and renewal diagnostic

Exploratory run date: 2026-10-01. This protocol is documented after exploration; it is not a preregistration. No daemon, CARLA run, learned model, or production scheduling claim is included. See the [research revision](../../research/update_20261001.md).

## Reproduce

Requires Python 3, NumPy, and Matplotlib (plot only). Run from the repository root. Outputs must be new directories; scripts refuse to replace existing runs.

```bash
python3 -m unittest discover -s experiments/research_update_20261001 -p 'test_*.py'
python3 experiments/research_update_20261001/audit_baselines.py --seeds 200 --out /tmp/mobi_baseline_audit_reproduction
python3 experiments/research_update_20261001/run_validity_probe.py --seeds 200 --out /tmp/mobi_validity_probe_reproduction
MPLBACKEND=Agg python3 experiments/research_update_20261001/plot_findings.py --results results/research_update_20261001
```

Archived results are under `results/research_update_20261001`. Each run manifest records source SHA-256, settings, and scope. Elapsed time is machine dependent. The source of the frozen September core is unchanged.

## Audit

`audit_baselines.py` adds a marginal-success ordered region-covering greedy that avoids duplicate channels in contention mode. It uses the same information as the old joint selector. It temporarily replaces the imported selection entry point and restores it afterward; no old source is edited.

Six configurations × five scenarios × three methods × 200 seeds = 18,000 episodes. Mean progress differences aggregate four actionable scenarios within each seed, then bootstrap 200 seed clusters 4,000 times. Permanent block remains in raw output. Selection enumeration covers 17 evidence states per region, 289 combinations per configuration. It is not a general policy equivalence proof.

The legacy simulator consumes random draws in action-dependent order. We retain it only for attribution of the old result. Same seeds therefore do not guarantee matched exogenous paths when actions differ. Five non-ideal configurations give identical audited selections and checked episode metrics for joint versus channel greedy; ideal has tied selection differences but zero progress gap.

## Validity probe

`validity_scheduler.py` is an exact tiny finite-horizon DP reference, not a novel algorithm. Ages increment each slot. A newly generated message arrives after one slot with age 1. All required regions must satisfy `age + action_guard <= ttl`. No evidence-content errors, changing required regions, physical geometry, or correlated channels are modeled. Correct free evidence and supplied TTLs are explicit assumptions.

Four TTL settings `(6,6)`, `(2,6)`, `(3,4,6)`, `(1,1)` × four methods × 200 seeds = 3,200 episodes, each 30 slots. One packet per slot, success probability 0.9, guard 1, rolling horizon 3. DP optimizes expected valid decision opportunities, then fewer sends; its horizon remains 3 near the end of the observation window. Ties are deterministic. Max-age and EDF are transparent comparators; myopic completion is a weak cold-start diagnostic.

Before executing any policy, the runner generates the complete per-seed, per-slot, per-region success table. Every method uses the same table and cannot inspect future entries. Confidence intervals resample paired seed differences (4,000 bootstrap samples). They measure uncertainty in this synthetic setup, not real-world driving risk. CSV includes unguarded-invalid opportunities as a proxy diagnostic, not measured collisions.

## Tests and limitations

Six tests check enumerated policy agreement, contention's conditional marginal change, action-time expiry, renewal order, agreement with exhaustive deterministic schedules, and impossible lifetime handling. They do not validate perception, wireless hardware, or CARLA safety. Source manifests are reproducibility records, not evidence of successful external replication.
