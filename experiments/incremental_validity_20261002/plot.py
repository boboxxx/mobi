#!/usr/bin/env python3
"""Finite retrospective comparisons; no independent-trial confidence intervals."""
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    selected = json.loads((a.results / 'selected_shared/analysis.json').read_bytes())['rows']
    all_rows = json.loads((a.results / 'all_shared/analysis.json').read_bytes())['rows']
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), gridspec_kw={'width_ratios': [1.5, 1]})
    methods = ['old', 'nearest', 'gap_greedy']
    labels = ['4/16 repair', 'Valid nearest', 'Gap greedy']
    colors = ['#757575', '#d89127', '#287c99']
    ax = axes[0]
    for i, identity in enumerate(['root_001', 'warm_000', 'warm_001']):
        for j, method in enumerate(methods):
            r = [x for x in selected if x['run'] == 'view0_repair_r1' and x['id'] == identity
                 and x['method'] == method and x['horizon_ms'] == 475]
            costs = [sum(x[k] for k in ['acquisition_ms', 'generation_ms', 'verification_ms', 'wire_ms']) for x in r]
            ax.scatter(costs, [i + (j - 1) * .19] * len(r), color=colors[j], s=38,
                       label=labels[j] if i == 0 else None, alpha=.8)
    ax.axvline(250, color='#222222', linestyle='--', linewidth=1)
    ax.set_xscale('log')
    ax.set_xticks([225, 250, 300, 400, 600, 800], ['225', '250', '300', '400', '600', '800'])
    ax.set_yticks(range(3), ['Root renewal', 'Warm 0', 'Warm 1'])
    ax.invert_yaxis()
    ax.set_xlabel('Observed + modeled total evidence age (ms)')
    ax.set_title('Selected difficulties: 475 ms sent lifetime')
    ax.legend(loc='lower right', frameon=False, fontsize=8)
    ax.grid(axis='x', alpha=.2)
    ax.text(.01, -.34, 'Dashed line: age <=250 ms permits a 200 ms action\nafter 50 ms tick rounding; each dot is one repeat.',
            transform=ax.transAxes, fontsize=8)
    ax = axes[1]
    for j, method in enumerate(methods):
        r = [x for x in all_rows if x['method'] == method]
        assert len(r) == 384
        passed = sum(x['hypothetical_action_pass'] for x in r)
        geometry = sum(x['geometry'] for x in r)
        counts = [passed, geometry - passed, 384 - geometry]
        bottom = 0
        for k, (n, col) in enumerate(zip(counts, ['#287c99', '#d89127', '#cccccc'])):
            ax.bar(j, n, bottom=bottom, color=col, width=.6,
                   label=['Timing passes', 'Valid but late', 'No packet'][k] if j == 0 else None)
            if n >= 20:
                ax.text(j, bottom + n / 2, str(n), ha='center', va='center', fontsize=9)
            bottom += n
    ax.set_ylim(0, 430)
    ax.set_ylabel('Archived input count')
    ax.set_xticks(range(3), ['4/16', 'Nearest', 'Gap greedy'])
    ax.set_title('All 384 inputs: shared projection')
    ax.legend(loc='upper center', ncol=1, fontsize=8, frameon=False, bbox_to_anchor=(.5, -.14))
    fig.suptitle('Same teacher history, unchanged full receiver, 20 ms + bytes/20 Mbps', fontsize=10)
    fig.subplots_adjust(bottom=.34, top=.82, wspace=.33)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix('.png'), dpi=180)
    fig.savefig(a.out.with_suffix('.pdf'))
    plt.close(fig)


if __name__ == '__main__':
    main()
