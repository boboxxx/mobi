# Same-frame receiver intersection: finite development reproduction

Read PROTOCOL.md and THEORY.md. Parent data and messages are unchanged:
`results/prospective_expiry_20261003`, published at b842980b8. The experiment
adds current-only cache/intersection processing and pays its observed extra
receiver cost, retaining the existing source/wire/decoder queues. It uses no
new simulator capture and fits no new risk statistic.

```
python experiments/view_intersection_20261004/audit.py \
  --parent results/prospective_expiry_20261003 \
  --results results/view_intersection_20261004 \
  --out results/view_intersection_20261004/audit_local.json
python experiments/view_intersection_20261004/summarize.py \
  --parent results/prospective_expiry_20261003 \
  --results results/view_intersection_20261004 \
  --out results/view_intersection_20261004/summary_local.json
python experiments/view_intersection_20261004/ambiguity.py \
  --parent results/prospective_expiry_20261003 \
  --results results/view_intersection_20261004 \
  --out results/view_intersection_20261004/ambiguity_local.json
python -m unittest discover -s experiments/view_intersection_20261004 -p 'test_*.py' -v
python experiments/view_intersection_20261004/verify_package.py
```

The accepted producer runs only onsheng; its saved measured costs are reused
by both independent auditors. Re-running evaluate.py gives another timing
realization and must use a separate output directory. It is not needed for
deterministic verification of the published sample.

The first producer aborted on identical discs: Decimal boundary rounding
discarded the only candidate. No accepted analysis was written. Original
kernel/tests/freeze and the failure log are retained. The revised kernel only
admits the identical-disc projection proposal; final primal feasibility and
integer dual checks are unchanged. numerical_revision.json documents the
exact change. All risk/data/model constants and parent bytes are unchanged.

Independent integer certificates bound modeled distance within2um and source
age within1us. The perfect modeled horizon is not the raw-compatible or
physical-world optimum. The inherited one-episode center-coverage failure
remains, including grants from that episode. No live link, ego control,
unknown inventory, new statistical holdout or MobiCom novelty is established.
No scheduler or recurring research loop was created.
