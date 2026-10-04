# Fixed independent-batch qualification and matched measured services

This supplement implements the capture protocol without changing frozen scores,
models, guard, scales, plan, labels, risk levels or geometry. Sources are pinned
in measurement_freeze.json before new calibration, test inference or profiling.
All previous capture/model freezes remain unchanged.

Qualification processes only calibration clouds first, writes calibration_frozen
and the zero-test-read ordering receipt, then processes test clouds. The max125
threshold per class/family includes every planned calibration episode, with six
sources grouped per episode. A failed or wholly empty episode has unbounded
unknown/refusal and score zero. All successful test frames and failures remain.
Whole-episode exclusions are reported separately from source-query overstatement
and paid grants. Simultaneous calibration confidence is 1-24*.95^125; empirical
60-test-episode upper bounds, when reported, do not imply conditional-grant risk.

Primary inference families: joint body/pose intersection lower bounds, fixed
ridge circle, guarded local mean+pose and guarded eight-mode union+pose. Local
variants plain and pair clip are diagnostic consequences of the SAME family
event and threshold. No threshold or guard is repaired from this batch.

Two honest-source initialized services per family:
* function sends hulls and the minimum family state (circle center, or mean/modes
  and scale, or fallback status); receiver evaluates the same registered queries;
* deadline performs exactly that family inference at the source and sends status
  and the two source-relative ages. The original source epoch is preserved.

Both services share one lightweight registration: class catalog, four thresholds,
calibration receipt, model/code digests, queries, motion, body and cap rules. The
source frontend, learned model and receiver integer-geometry implementation are
installed before profiles. Cold is measured transfer/verification of necessary
registration, not installation or a cold process. No full background point map,
model weights or unused source-only metadata is charged to the receiver.

Every test row gets three actual source and receiver profiles per each of eight
methods. Order is lexicographic SHA256(row_id+'|'+iteration+'|'+method), ascending.
Source measurement includes observed XYZ extraction, frozen static frontend,
native hull construction, family prediction and encoding, plus same captured
stride-copy fee. Deadline source additionally runs the actual family inference;
function receiver runs it after decoding. Disk loading and model preparation
are service initialization/input access, not invented per-packet costs. Profiles
exclude diagnostic labels and all source inputs remain XYZ/layout/known class.
Max measured profile fees are descriptive, not worst-case execution bounds.

Three FIFO stages: source, link and receiver; 20/2Mbit/s, propagation20ms,
reserve220ms, two fixed +/-6m queries, sixteen50ms query times per planned test
episode including failures. Lightweight setup is identical across all methods.
Exact integer wire fields, checksums, registered calibration/model hashes,
source epochs and queue timing are independently replayed. The predictor replay
is explicitly shared; raster, hull inclusion, score/geometry, calibration and
policy arithmetic are independently reconstructed from raw data.

This is a finite static-RSU/moving-actor trace study. No live ego policy, wireless
measurement, unknown-scene inventory, authorization-conditional safety, new
conformal theorem or standalone set-geometry novelty is established.
