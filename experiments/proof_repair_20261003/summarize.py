#!/usr/bin/env python3
"""Cost all fixed and adaptive trials, without selecting winning budgets/trials."""
import argparse
import hashlib
import json
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    prior = ROOT / 'results/tube_evidence_20261003'
    cold = json.loads((prior / 'replay/cold.json').read_text())
    costs = json.loads((prior / 'costs_sheng.json').read_text())['rows']
    sources = {x['case']: x for x in json.loads((ROOT / 'results/pose_inversion_20261003/replay/sources.json').read_text())}

    def initialization(row):
        c = next(c for c in cold if c['proof'] == row['proof'])
        us = math.ceil((c['total_s'] + c['reference_encode_s'] + row['restore_s']) * 1e6
                       + max(r['encode_ns'] + r['decode_ns'] for r in costs if r['reference'] == c['reference']) / 1000
                       + c['reference_install_bytes'] * .4 + 40000)
        gap = math.floor((row['source_timestamp'] - sources[row['old_case']]['source_timestamp']) * 1e6)
        return dict(bootstrap_us=us, source_gap_us=gap, initialization_wait_us=max(0, us-gap))

    fixed = []
    for r in json.loads((a.results / 'replay/rows.json').read_text()):
        init = initialization(r)
        base = 240000 + init['initialization_wait_us'] + r['wire_bytes']*.4 + r['packet_encode_s']*1e6
        total = max(t['encode_s'] + t['receiver_s'] for t in r['timings'])*1e6
        direct = max(t['encode_s'] + t['baseline_s'] for t in r['timings'])*1e6
        rr = {k:r[k] for k in ('blueprint','query_index','radius_um','sigma','budget','baseline_lower_us','lower_us','upper_us','visits')}
        rr.update(init)
        rr.update(remaining_us=max(0, r['lower_us']-math.ceil(base+total)),
                  direct_remaining_us=max(0, r['baseline_lower_us']-math.ceil(base+direct)),
                  median_receiver_us=st.median(t['receiver_s'] for t in r['timings'])*1e6,
                  median_direct_receiver_us=st.median(t['baseline_s'] for t in r['timings'])*1e6,
                  worst_receiver_and_encode_us=total)
        fixed.append(rr)
    groups = []
    for budget in (0,256,4096):
        rs = [r for r in fixed if r['budget']==budget]
        assert len(rs)==36
        groups.append(dict(budget=budget, tasks=len(rs), positive_remaining=sum(r['remaining_us']>0 for r in rs),
                           improved_lower=sum(r['lower_us']>r['baseline_lower_us'] for r in rs),
                           median_receiver_us=st.median(r['median_receiver_us'] for r in rs),
                           median_lower_improvement_us=st.median(r['lower_us']-r['baseline_lower_us'] for r in rs)))
    direct = [r for r in fixed if r['budget']==0]
    baseline = dict(tasks=36, positive_remaining=sum(r['direct_remaining_us']>0 for r in direct),
                    median_receiver_us=st.median(r['median_direct_receiver_us'] for r in direct),
                    source='Direct revalidation timings inside the budget-0 trials; excludes repair wrapper overhead.')
    adaptive = json.loads((a.results / 'adaptive/rows.json').read_text())
    tasks = defaultdict(list)
    for r in adaptive:
        r.update(initialization(r))
        # The causal experiment did not budget initialization backlog. Verify that
        # the declared saved-observation gap really pays it before accepting it.
        assert r['initialization_wait_us']==0, 'Adaptive policy invalid with unpaid bootstrap wait'
        assert r['remaining_us']==max(0,r['lower_us']-math.ceil(r['external_us']+r['receiver_s']*1e6))
        tasks[(r['blueprint'],r['query_index'],r['radius_um'])].append(r)
    grouped = []
    for key, rs in tasks.items():
        assert len(rs)==3 and sorted(r['repeat'] for r in rs)==[0,1,2]
        grouped.append(dict(blueprint=key[0],query_index=key[1],radius_um=key[2],
                            positive_trials=sum(r['remaining_us']>0 for r in rs),
                            direct_positive_trials=sum(r['baseline_remaining_us']>0 for r in rs),
                            min_remaining_us=min(r['remaining_us'] for r in rs),
                            max_remaining_us=max(r['remaining_us'] for r in rs),
                            min_direct_remaining_us=min(r['baseline_remaining_us'] for r in rs),
                            max_direct_remaining_us=max(r['baseline_remaining_us'] for r in rs),
                            visits=[r['visits'] for r in rs],
                            median_receiver_us=st.median(r['receiver_s'] for r in rs)*1e6,
                            median_direct_receiver_us=st.median(r['baseline_s'] for r in rs)*1e6))
    adaptive_summary = dict(tasks=len(tasks),trials=len(adaptive),
        positive_trials=sum(r['remaining_us']>0 for r in adaptive),
        direct_positive_trials=sum(r['baseline_remaining_us']>0 for r in adaptive),
        all_three_positive_tasks=sum(g['positive_trials']==3 for g in grouped),
        direct_all_three_positive_tasks=sum(g['direct_positive_trials']==3 for g in grouped),
        mixed_outcome_tasks=sum(0<g['positive_trials']<3 for g in grouped),
        direct_mixed_outcome_tasks=sum(0<g['direct_positive_trials']<3 for g in grouped),
        gate_counts=dict(sorted(Counter(str(r['gate'][0]) for r in adaptive).items())),
        median_receiver_us=st.median(r['receiver_s'] for r in adaptive)*1e6,
        median_direct_receiver_us=st.median(r['baseline_s'] for r in adaptive)*1e6,
        actual_lower_improvements=sum(r['lower_us']>r['baseline_lower_us'] for r in adaptive))
    audits={name:{k:v for k,v in json.loads((a.results/name).read_text()).items() if k not in ('rows','scope')}
            for name in ('audit_sheng.json','audit_adaptive_sheng.json')}
    out=dict(fixed_rows=fixed,fixed_groups=groups,fixed_direct_baseline=baseline,
             adaptive_tasks=grouped,adaptive_summary=adaptive_summary,audits=audits,
             bootstrap_range_us=[min(r['bootstrap_us'] for r in fixed+adaptive),max(r['bootstrap_us'] for r in fixed+adaptive)],
             max_initialization_wait_us=max(r['initialization_wait_us'] for r in fixed+adaptive),
             source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             scope='All 36 selected tasks retained. Fixed rows charge worst of three observed encode+receiver times; adaptive rows retain each causal timing-dependent trial and require all three positive for a task count. Paid cold initialization and restore fit the 20.5s saved-data gap. 20Mbps wire,20ms propagation,20ms clock and200ms action reserve are modeled. No sensor/callback delay, WCET, real network, concurrent queries, independent risk validation or physical safety claim. Adaptive policy developed after inspecting fixed-budget results on the same data; no best-budget or best-trial selection.')
    a.out.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':
    main()
