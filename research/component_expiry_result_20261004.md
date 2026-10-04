# Separate component evidence expiry: finite development result

Two-component candidate frozen and published at0deba1a7a before sheng execution.
All previously examined data remain development. 6240 frame scores and3972 test
geometries were independently reconstructed on sheng and locally. Audit receipts
match byte-for-byte. Five meaningful boundary, equivalence and exact confidence
budget tests passed before/after execution. No new capture or certification yet.

The earlier typed fallback candidate multiplied an unrelated supported-score Q
by body radius. The new method calibrates supported errors and fallback μm slack
separately, sharing one fallback threshold across the two supported families.
At runtime the frozen observable guard selects its set; truth is only offline.
This preserves supported pose/circle constraints and avoids fallback contaminating
the learned radius. Empty observation refuses.

|Class|Mean P95 ms|Modes P95 ms|Queries increased/decreased, mean|Queries increased/decreased, modes|
|---|---:|---:|---:|---:|
|Audi|113.441|153.104|0/0|0/0|
|Tesla|135.146|203.819|4/0|4/0|
|Sprinter|289.128|223.120|2/0|2/0|
|Bicycle|91.453|80.991|2/0|2/0|
|Motorcycle|77.920|78.553|203/0|207/0|
|Walker|33.821|28.957|0/0|0/0|

Relative to original local methods there are ZERO decreased source queries
across all six classes; mean211 and modes215 increased queries. Motorcycle P95
oracle-minus-authorized-source-age gap improves179.461→77.920ms (mean) and
179.461→78.553ms (modes), respectively56.58% and56.23% reduction. Other classes
retain their P95, with Sprinter mean improving slightly. Zero measured age
overstatements do not erase the excluded episodes: mean Audi1/Motorcycle1;
modes Sprinter1/Bicycle2/Motorcycle1/Walker1, per60 planned episodes/class.
The method can exclude a center yet produce conservative ages at these queries.

This development outcome passes the practical regression gate that both earlier
fallback candidates failed. It does not certify risk, query-conditional safety,
unknown actors, distribution shift, live ego control or MobiCom novelty. Separate
maxima need additional samples: target2.5% per component, shared fallback counted
once gives18 events. A genuinely new n260/class calibration batch has confidence
error≤18(0.975)^260; adding four baseline families at5% gives total≤0.024954428.
The marginal union risk per proposed family is≤5% on the fixed full-episode law.

Conditional on authorization requires a separate certificate. One independently
chosen query from each IID certification episode is the sample unit. Exact
binomial selective testing and multiple testing correction follow existing
[Learn then Test, section3.2](https://arxiv.org/html/2110.01052v5); they are not
claimed as a new theorem. New independent calibration, policy certification and
test must run before deployment claims. Raw development outcomes are not reused
as independent certification data.
