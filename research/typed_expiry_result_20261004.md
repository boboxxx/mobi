# Typed fallback finite development result

Status: finite development and independent reconstruction complete on sheng;
not an independent qualification and not completion of the research project.
The score was designed after examining the previous test corpus. All 1110
planned prior episodes, including previous test outcomes, are development.
No new CARLA capture, policy certification, radio timing or live ego run occurred.

The candidate preserves the supported pose unit10mm and circle unitσ, changing
only fallback normalization to the known body radius. Two families were frozen
and published at ae3c3c5103a6d5b1c739b95b17b9c2957efd8630 before execution.
6240 frame scores and 3972 test-frame geometries were independently reconstructed
on sheng and locally, with byte-identical audit receipts. All five meaningful
boundary and equivalence tests passed before and after execution. There were
zero fixed-query age overstatements, but nonzero excluded episodes remain.

|Class|Original mean/modes P95 ms|Typed mean/modes P95 ms|Excluded episodes mean/modes|
|---|---:|---:|---:|
|Audi|113.441/153.104|117.559/154.564|1/0|
|Tesla|135.146/203.819|151.109/205.940|0/0|
|Sprinter|289.132/223.120|299.954/234.942|0/1|
|Bicycle|91.453/80.991|92.748/81.829|0/2|
|Motorcycle|179.461/179.461|78.071/81.732|1/1|
|Walker|33.821/28.957|34.098/29.595|0/1|

The supported geometry equals the original geometry at the same Q. For five
classes Q is unchanged; every reduction in their source ages comes from
fallback. The complete diagnosis retains all 50 decreased source queries
across both families, including motorcycles: every decrease is fallback.
A small number of large fallback losses can move P95 even when most queries
are unchanged. Body-normalized fallback uses δ=Qb, which is unnecessarily large
for the observed fallback geometric errors. This candidate is rejected as a
global replacement; the motorcycle improvement alone does not satisfy the goal.

The next candidate will separately calibrate supported errors and fallback
geometric slack, with explicit whole-episode union risk accounting. Independent
thresholds alone do not grant a new conditional coverage theorem. In particular,
P(center exclusion) and P(exclusion | granted action) must be verified separately.
Learn then Test already establishes exact-binomial selective risk control:
[author manuscript, section3.2](https://arxiv.org/html/2110.01052v5).

Reproduce with the experiment README; raw parent inputs, fixed predictors and
native geometry are inherited from the published previous experiment. No
post-result edits of the frozen method are required or permitted.
