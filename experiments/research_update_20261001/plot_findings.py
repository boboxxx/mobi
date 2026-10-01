#!/usr/bin/env python3
"""Plot archived CSV estimates; synthetic progress and validity are distinct."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results', type=Path, required=True)
    args = p.parse_args()
    audit = read(args.results / 'baseline_audit/paired_comparisons.csv')
    probe = read(args.results / 'validity_probe/paired_comparisons.csv')
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), constrained_layout=True)
    ax = axes[0]
    configs = ['independent', 'contention', 'burst']
    for j, (baseline, label, color) in enumerate([
        ('coverage_greedy', 'Original coverage baseline', '#c27630'),
        ('channel_greedy', 'Channel-aware greedy', '#246b91'),
    ]):
        rows = [next(r for r in audit if r['config'] == c and r['baseline'] == baseline) for c in configs]
        val = np.array([float(r['progress_diff']) for r in rows]) * 100
        lo = np.array([float(r['ci_low']) for r in rows]) * 100
        hi = np.array([float(r['ci_high']) for r in rows]) * 100
        ax.errorbar(np.arange(3) + (j - .5)*.18, val, yerr=[val-lo, hi-val],
                    fmt='o', capsize=4, color=color, label=label)
    ax.set_xticks(range(3), ['Independent', 'Contention', 'Burst'])
    ax.set_ylabel('Joint selector − baseline progress (pp)')
    ax.set_title('A. Old gain disappears with channel-aware greedy')
    ax.legend(frameon=False, fontsize=9, loc='upper left')
    ax.set_ylim(-4, 37)
    ax = axes[1]
    configs = ['uniform', 'heterogeneous', 'three_regions', 'impossible']
    rows = [next(r for r in probe if r['config'] == c and r['baseline'] == 'edf') for c in configs]
    val = np.array([float(r['diff']) for r in rows]) * 100
    lo = np.array([float(r['ci_low']) for r in rows]) * 100
    hi = np.array([float(r['ci_high']) for r in rows]) * 100
    ax.errorbar(range(4), val, yerr=[val-lo, hi-val], fmt='o', capsize=4, color='#246b91')
    ax.set_xticks(range(4), ['(6, 6)', '(2, 6)', '(3, 4, 6)', '(1, 1)'])
    ax.set_xlabel('Supplied evidence lifetimes (slots)')
    ax.set_ylabel('Three-step DP − EDF valid opportunities (pp)')
    ax.set_title('B. Renewal order helps in heterogeneous cases')
    ax.set_ylim(-2, 17)
    for i, value in enumerate(val):
        ax.annotate(f'{value:+.2f}', (i, hi[i]), xytext=(0, 7), textcoords='offset points', ha='center', fontsize=10)
    for ax in axes:
        ax.axhline(0, color='#666666', lw=.8, ls='--')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=.16)
    fig.suptitle('Finite synthetic diagnostics • 200 seed clusters • paired bootstrap 95% intervals\nKnown lifetimes and correct free evidence; no new CARLA evaluation', fontsize=11)
    fig.savefig(args.results / 'findings.png', dpi=180)
    fig.savefig(args.results / 'findings.pdf')


if __name__ == '__main__':
    main()
