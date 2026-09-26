#!/usr/bin/env python3
"""Finite evidence/network model shared by the mechanism and CARLA runs."""
from dataclasses import dataclass
import itertools
import math
import random

REGIONS = ("A", "B")


@dataclass(frozen=True)
class Provider:
    name: str
    region: str
    channel: int
    marginal: float
    delay: int
    size: int = 48


PROVIDERS = (
    Provider("A0", "A", 0, .92, 1),
    Provider("B0", "B", 0, .92, 1),
    Provider("A1", "A", 1, .80, 1),
    Provider("B1", "B", 1, .80, 1),
)
PROVIDER = {p.name: p for p in PROVIDERS}


CONFIGS = {
    "ideal": dict(slots=2, deadline=1, ttl=3, mode="ideal"),
    "independent": dict(slots=2, deadline=1, ttl=3, mode="independent"),
    "contention": dict(slots=2, deadline=1, ttl=3, mode="contention"),
    "burst": dict(slots=2, deadline=1, ttl=3, mode="burst"),
    "short_deadline": dict(slots=2, deadline=1, ttl=3, mode="short_deadline"),
    "one_slot": dict(slots=1, deadline=1, ttl=3, mode="independent"),
}

METHODS = ("no_comm", "round_robin", "coverage_greedy", "singleton_voi",
           "set_independent", "set_joint", "full_info")


def effective_delay(provider, config):
    if config["mode"] == "short_deadline" and provider.channel == 1:
        return 2
    return provider.delay


def marginal_success(provider, config):
    if effective_delay(provider, config) > config["deadline"]:
        return 0.0
    if config["mode"] == "ideal":
        return 1.0
    if config["mode"] == "burst":
        # Marginal after a 20% channel-wide bad state.
        return .8 * .98
    return provider.marginal


def joint_success(names, config, assume_independent=False):
    ps = [PROVIDER[n] for n in names]
    if not ps:
        return 0.0
    if any(effective_delay(p, config) > config["deadline"] for p in ps):
        return 0.0
    if assume_independent or config["mode"] in ("ideal", "independent", "short_deadline"):
        answer = 1.0
        for p in ps:
            answer *= marginal_success(p, config)
        return answer
    if config["mode"] == "contention" and len(ps) > 1 and len({p.channel for p in ps}) == 1:
        return 0.0
    if config["mode"] == "burst" and len(ps) > 1 and len({p.channel for p in ps}) == 1:
        return .8 * (.98 ** len(ps))
    answer = 1.0
    for p in ps:
        answer *= marginal_success(p, config)
    return answer


def fresh(evidence, region, cycle, ttl):
    item = evidence.get(region)
    return item is not None and cycle - item[1] <= ttl


def unresolved_regions(evidence, cycle, ttl):
    return [r for r in REGIONS if not fresh(evidence, r, cycle, ttl)]


def select_messages(method, evidence, cycle, config):
    slots = config["slots"]
    if method in ("no_comm", "full_info"):
        return []
    if method == "round_robin":
        order = (("A0", "B0"), ("A1", "B1"))[cycle % 2]
        return list(order[:slots])
    missing = unresolved_regions(evidence, cycle, config["ttl"])
    if not missing:
        # Refresh the oldest evidence before it expires.
        ages = sorted(REGIONS, key=lambda r: evidence[r][1])
        missing = ages[:max(1, slots)]
    candidates = [p for p in PROVIDERS if p.region in missing]
    if method in ("coverage_greedy", "singleton_voi"):
        chosen = []
        for region in missing:
            options = [p for p in candidates if p.region == region]
            if not options or len(chosen) >= slots:
                continue
            # singleton_voi differs only in the age/uncertainty multiplier; within
            # a region it still chooses the best marginal evidence per byte.
            chosen.append(max(options, key=lambda p: marginal_success(p, config) / p.size).name)
        if len(chosen) < slots:
            remaining = [p for p in PROVIDERS if p.name not in chosen]
            remaining.sort(key=lambda p: marginal_success(p, config) / p.size, reverse=True)
            for p in remaining:
                if p.region not in {PROVIDER[n].region for n in chosen}:
                    chosen.append(p.name)
                if len(chosen) == slots:
                    break
        return chosen
    if method in ("set_independent", "set_joint"):
        best = None
        for k in range(1, min(slots, len(PROVIDERS)) + 1):
            for subset in itertools.combinations(PROVIDERS, k):
                regions = {p.region for p in subset}
                newly = len(regions.intersection(missing))
                if newly == 0:
                    continue
                # Decision sufficiency is lexicographic: cover unresolved critical
                # regions, then maximize probability they jointly arrive, then bytes.
                sufficiency = 1 if set(missing).issubset(regions) else 0
                probability = joint_success([p.name for p in subset], config,
                                            assume_independent=(method == "set_independent"))
                key = (sufficiency, probability, newly, -sum(p.size for p in subset),
                       tuple(p.name for p in subset))
                if best is None or key > best[0]:
                    best = (key, [p.name for p in subset])
        return best[1] if best else []
    raise ValueError(method)


def deliver(names, config, rng):
    """Return provider names delivered before the configured decision deadline."""
    ps = [PROVIDER[n] for n in names]
    eligible = [p for p in ps if effective_delay(p, config) <= config["deadline"]]
    mode = config["mode"]
    if mode == "ideal":
        return [p.name for p in eligible]
    if mode == "contention":
        delivered = []
        for channel, group in itertools.groupby(sorted(eligible, key=lambda p:p.channel), key=lambda p:p.channel):
            group = list(group)
            if len(group) > 1:
                winner = rng.choice(group)
                if rng.random() < winner.marginal:
                    delivered.append(winner.name)
            elif group and rng.random() < group[0].marginal:
                delivered.append(group[0].name)
        return delivered
    if mode == "burst":
        delivered = []
        for channel, group in itertools.groupby(sorted(eligible, key=lambda p:p.channel), key=lambda p:p.channel):
            group = list(group)
            good = rng.random() >= .2
            if good:
                delivered.extend(p.name for p in group if rng.random() < .98)
        return delivered
    return [p.name for p in eligible if rng.random() < p.marginal]


def scenario_state(name, cycle, clear_cycle=15):
    if name == "free":
        return {"A":"free", "B":"free"}
    if name == "hazard_a":
        return {"A":"occupied" if cycle < clear_cycle else "free", "B":"free"}
    if name == "hazard_b":
        return {"A":"free", "B":"occupied" if cycle < clear_cycle else "free"}
    if name == "both_hazard":
        value = "occupied" if cycle < clear_cycle else "free"
        return {"A":value, "B":value}
    if name == "permanent_block":
        return {"A":"occupied", "B":"free"}
    raise ValueError(name)


def reference_clear_cycle(name, clear_cycle=15):
    if name == "free": return 0
    if name in ("hazard_a", "hazard_b", "both_hazard"): return clear_cycle
    return None


def run_episode(method, config_name, scenario, seed, horizon=50, clear_cycle=15,
                false_free=.01, false_occupied=.03):
    config = CONFIGS[config_name]
    rng = random.Random(seed)
    evidence = {}
    scheduled = delivered_count = useful = deadline_drop = 0
    bytes_sent = 0
    go_cycles = []
    unsafe_go = 0
    first_go_after_clear = None
    clear_at = reference_clear_cycle(scenario, clear_cycle)
    selections = []
    pending = []
    for cycle in range(horizon):
        state = scenario_state(scenario, cycle, clear_cycle)
        arrived_now = [x for x in pending if x[0] == cycle]
        pending = [x for x in pending if x[0] != cycle]
        for _, name, observed, produced_cycle in arrived_now:
            p = PROVIDER[name]
            before = evidence.get(p.region)
            evidence[p.region] = (observed, produced_cycle, name)
            delivered_count += 1
            if before is None or before[0] != observed or cycle - before[1] > config["ttl"]:
                useful += 1
        if method == "full_info":
            evidence = {r:(state[r], cycle, "full_info") for r in REGIONS}
            names = []
        else:
            names = select_messages(method, evidence, cycle, config)
            selections.append(tuple(names))
            scheduled += len(names); bytes_sent += sum(PROVIDER[n].size for n in names)
            arrived = deliver(names, config, rng)
            deadline_drop += len(names) - len(arrived)
            for name in arrived:
                p = PROVIDER[name]; observed = state[p.region]
                u = rng.random()
                if observed == "occupied" and u < false_free:
                    observed = "free"
                elif observed == "free" and u < false_occupied:
                    observed = "occupied"
                pending.append((cycle + effective_delay(p, config), name, observed, cycle))
        is_fresh = all(fresh(evidence, r, cycle, config["ttl"]) for r in REGIONS)
        go = is_fresh and all(evidence[r][0] == "free" for r in REGIONS)
        if go:
            go_cycles.append(cycle)
            if not all(state[r] == "free" for r in REGIONS):
                unsafe_go += 1
            if clear_at is not None and cycle >= clear_at and first_go_after_clear is None:
                first_go_after_clear = cycle
    clear_den = (horizon - clear_at) if clear_at is not None else 0
    progress_fraction = (sum(c >= clear_at for c in go_cycles) / clear_den
                         if clear_at is not None and clear_den else 0.0)
    delay = (first_go_after_clear - clear_at if first_go_after_clear is not None and clear_at is not None
             else (horizon - clear_at if clear_at is not None else math.nan))
    return dict(method=method, config=config_name, scenario=scenario, seed=seed,
                horizon_cycles=horizon, clear_cycle=clear_at, progress_fraction=progress_fraction,
                decision_delay_cycles=delay, unsafe_go_fraction=unsafe_go/horizon,
                first_go_cycle=first_go_after_clear, scheduled_messages=scheduled,
                delivered_messages=delivered_count, useful_messages=useful,
                dropped_or_late_messages=deadline_drop, bytes_sent=bytes_sent,
                useful_bytes_per_go=(bytes_sent/max(1,len(go_cycles))),
                valid_go_cycles=len(go_cycles), selection_signature=str(selections[:6]))
