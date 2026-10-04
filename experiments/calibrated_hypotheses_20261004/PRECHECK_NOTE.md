# Synthetic probe correction before fitting

The first pruning unit scenario used a single near-origin rectangle. Both max
and clip ages saturated at500ms, so a strict age-improvement assertion failed.
The corrected scenario includes a second observation component at the query and
a learned mode at7m incompatible with both observed components. This directly
tests exact pair pruning versus a global max bound. No data/model/experiment
output existed. Retain first_probe_test.py for the original scenario; it is
excluded from test_*.py discovery.
