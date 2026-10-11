import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--science', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
d = json.loads(args.science.read_bytes())
methods = ('snapshot', 'factorized', 'joint')
names = ('Current only', 'History intervals', 'History joint')
fig, axes = plt.subplots(1, 3, figsize=(13, 3.7), constrained_layout=True)
count = d['summary']['queries']
for i, m in enumerate(methods):
    s = d['summary']['methods'][m]
    full = s['paid_allowed']-s['selected_censored']
    axes[0].bar(i, full, color='#337f8d')
    axes[0].bar(i, s['selected_censored'], bottom=full, color='#c9dfe2', hatch='//')
    axes[0].text(i, s['paid_allowed']+17, str(s['paid_allowed']), ha='center')
axes[0].set_xticks(range(3), names, rotation=15)
axes[0].set_ylim(0, 900)
axes[0].set_ylabel('Allowed paid queries / %d' % count)
axes[0].set_title('Same observations and fees')
axes[0].text(.03, .97, 'Hatch: future audit censored', transform=axes[0].transAxes, va='top', fontsize=9)
for m, color, label in zip(('snapshot', 'factorized'), ('#b46f40', '#337f8d'), names):
    expiry = sorted(q['methods'][m]['expiry_us']/1000 for e in d['episodes'] for s in e['sources'] for q in s['queries'])
    axes[1].step(expiry, np.arange(1, len(expiry)+1)/len(expiry), where='post', label=label, color=color)
axes[1].set(xlabel='Proven source prefix (ms)', ylabel='Fraction of queries', title='Conditional geometric prefixes', xlim=(0, 510), ylim=(0, 1.04))
axes[1].legend(loc='upper left', frameon=False)
x, y, labels = [], [], []
for e in d['episodes']:
    if e['status'] == 'captured':
        x.append(sum(q['methods']['snapshot']['paid_allowed'] for s in e['sources'] for q in s['queries']))
        y.append(sum(q['methods']['factorized']['paid_allowed'] for s in e['sources'] for q in s['queries']))
        labels.append(e['motion'])
for motion, color in zip(('stay', 'away', 'approach', 'cross'), ('#6b6b6b', '#337f8d', '#b46f40', '#79558b')):
    ids = [i for i, m in enumerate(labels) if m == motion]
    axes[2].scatter([x[i] for i in ids], [y[i] for i in ids], label=motion, color=color, alpha=.75)
axes[2].plot([0, 60], [0, 60], '--', color='#aaa', linewidth=1)
axes[2].set(xlabel='Current-only paid permits / 60', ylabel='History paid permits / 60', title='22 captured scenes, paired', xlim=(-2, 62), ylim=(-2, 62))
axes[2].legend(frameon=False, fontsize=8)
for ax in axes:
    ax.spines[['top', 'right']].set_visible(False)
fig.savefig(args.out, dpi=180)
