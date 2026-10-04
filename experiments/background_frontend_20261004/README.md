# Static-background frontend diagnostic

Read PROTOCOL.md first. This finite study changes the observation-to-state frontend
while retaining all parent raw bytes. It fits a fixed per-layout background from
old calibration step-zero XYZ scans and examines all current prospective scans
with unshifted and declared1/10mm coordinate shifts. It is post-result development:
new max95 radii are descriptive, with no new untouched risk qualification.

```
python experiments/background_frontend_20261004/audit.py \
 --results results/background_frontend_20261004 \
 --out results/background_frontend_20261004/audit_local.json
python experiments/background_frontend_20261004/summarize.py \
 --results results/background_frontend_20261004 \
 --out results/background_frontend_20261004/summary_local.json
python -m unittest discover -s experiments/background_frontend_20261004 -p 'test_*.py' -v
```

The producer ran onsheng once; both auditors reuse its saved timings. Extraction
samples cover world transformation, subtraction, component extraction and center
quantization, not full sensor acquisition, packet encoding, wire/decoder queues
or action execution. Geometry>=220ms is a source-time diagnostic and must not be
called a paid/received grant. Full background provenance and transfer bytes are
saved, including the fitted static voxel reference. A changed or unseen basis or
scene requires separate validation; subtracting static voxels is not proof that
unknown dynamic objects are absent.

IDs, actor truth and tags never enter fit counts or the online extract() interface.
IDs are used only after extraction to count removed target returns, and centers
only for development residual/coverage audits. Empty output refuses authority.
Production geometry uses the original integer lifetime engine; the separate
auditor uses sorted voxel tuples, scipy raster components, Decimal coverage and
independent analytic+integer endpoint checks. Parent code and results stay fixed.
No simulator, live link, ego control, new SOTA comparison or MobiCom contribution
is established by this diagnostic. No recurring research job is created.

The separate post-result body-support hypothesis is described in BODY_SUPPORT_NOTE.md.
It has no computed expiry or paid utility. Deterministic verification also runs:

```
python experiments/background_frontend_20261004/body_support_audit.py \
 --results results/background_frontend_20261004 \
 --body results/background_frontend_20261004/body_support_sheng.json \
 --out results/background_frontend_20261004/body_support_audit_local.json
python experiments/background_frontend_20261004/verify_package.py
```

The initial merge display files differ only by at most8.89e-16m host arithmetic;
original versions are archived. Nine-place display normalization is unrelated to
producer geometry. The first local float-score body helper is also archived;
exact integer scores remove its artificial1um slack without changing the accepted
background producer. Five accepted JSON pairs match bytewise across hosts.
