"""Plot complete physical traces and separate post-result computation replay."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

P = Path('results/closed_loop_motion_20261011')
analysis = json.loads((P/'analysis_sheng.json').read_bytes())
bench = json.loads((P/'benchmark_sheng.json').read_bytes())
fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
for method, color, offset in (('history', '#176d9c', -.13), ('snapshot', '#dc702b', .13)):
    rows = [e for e in analysis['episodes'] if e['method']==method and e['status']=='captured']
    axes[0].scatter([e['pair']+offset for e in rows], [e['max_progress_m'] for e in rows], color=color, label=method, s=42)
axes[0].axhline(11, color='black', linestyle='--', linewidth=1, label='Route goal')
axes[0].set_xticks(range(6), ['away -', 'away +', 'clear -', 'clear +', 'approach -', 'approach +'], rotation=35)
axes[0].set_ylabel('Maximum physical progress (m)')
axes[0].set_title('11 complete traces; 0 routes completed')
axes[0].text(2.3, 6.5, 'History clear +: missing trace\n(storage failure; progress unknown)', fontsize=8)
axes[0].legend(fontsize=8, loc='upper left')
for key, label, color in (('original_us', 'Original', '#176d9c'), ('fast_us', 'Exact CAP early stop', '#dc702b')):
    values = np.sort(np.asarray(bench[key]))
    axes[1].plot(values, np.arange(1, len(values)+1)/len(values), color=color, label=label)
axes[1].set_xscale('log')
axes[1].set_xlabel('Measured sheng replay query cost (us)')
axes[1].set_ylabel('Empirical CDF')
axes[1].set_title('6,905 same-query replays; identical expiry')
axes[1].legend(fontsize=8)
for axis in axes:
    axis.grid(alpha=.2)
fig.savefig(P/'closed_loop_and_replay.png', dpi=200)
plt.close(fig)
