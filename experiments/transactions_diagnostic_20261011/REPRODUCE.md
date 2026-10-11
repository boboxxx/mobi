# Reproduce the finite 2026-10-11 diagnostics

Run from repository root with Python3.8 or later. Core probability code uses
only the standard library. Matplotlib is needed only for the figure. Existing
historical outputs must be preserved; select fresh output directories.

```
python -m unittest discover -s experiments/action_window_reference_20261011 -p test_reference.py -v
python experiments/action_window_reference_20261011/run.py --out /tmp/action-window-fresh/local
python experiments/temporal_action_window_20261011/run.py --out /tmp/temporal-window-fresh/local
cmp /tmp/action-window-fresh/local/scientific.json results/action_window_reference_20261011/local/scientific.json
cmp /tmp/temporal-window-fresh/local/scientific.json results/temporal_action_window_20261011/local/scientific.json
python experiments/transactions_diagnostic_20261011/check_codec.py
python experiments/transactions_diagnostic_20261011/audit.py --host local --out /tmp/action-window-independent-audit.json
python experiments/transactions_diagnostic_20261011/verify_package.py --out /tmp/action-window-package-verification.json
```

Source freezes are checked before either run. scientific.json is deterministic;
runtime.json records host-specific timings and must not be compared byte-wise.
The independent auditor reconstructs distributions using a different explicit
state update, preserves production results and adds a clearly post-result
source-state oracle diagnosis. Local/sheng audit numeric receipts agree; their
input-path strings differ by the host subdirectory. Central package verification
checks that this is the only difference.

This experiment does not require CARLA, GPU, live V2X or a traffic dataset.
Its probabilities are exact under declared synthetic laws and are not learned
from real partial observations. Empty selection does not certify useful driving.
The result/report and paper-read log explicitly retain these limitations.
