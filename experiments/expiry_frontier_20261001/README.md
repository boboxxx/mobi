# Maximum horizon of a fixed-region evidence certificate

Finite, source-backed **post-analysis** of the eight live-repair runs. This is
not an online driving result. `THEORY.md` gives the equivalence to the existing
conservative tile verifier and the conditional physical scope.

From the repository root (Python 3.8+, NumPy/SciPy):

```bash
python -m unittest discover -s experiments/expiry_frontier_20261001
python experiments/expiry_frontier_20261001/study.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-expiry-frontier-replay
```

The output directory must not exist. 28 selected actual frames give 37 full-ray
or transmitted-subset cases, 807 reference comparisons and 9 fully reverified
packets. The 2 s search cap, input selection and timing scope were frozen in
`PROTOCOL.md` before this diagnostic. All quantities are conditional on the
existing sensing/shape/motion contracts. Maximum means the largest integer
microsecond accepted by the fixed-region tile certificate, not a physically
optimal or unconditionally safe lifetime. Nonzero full-ray output may exceed
the legal packet ray count. Timing is measured component cost, not WCET.

`root_ready` diagnoses the old prospective float/integer discrepancy. The later
production-entry correction is in `../live_repair_20261001/deadline.py`, with a
conservative next-step reservation and an actual-reference check still required.
