# V2X Evidence Scheduling toward MobiCom 2027

Finite experiments and literature-driven audits for semantic V2X scheduling. The latest research revision is dated **2026-10-01**; historical September code and data are retained for reproducibility.

## Main finding

**Latest: policy-conditioned validity and actual actuator diagnostics.** New sheng work adds 30 CARLA own-vehicle episodes, 180 paired geometry checks and 1,044 paired current-ray renewals. Restricting execution to a hold/go/brake policy extends the largest passing grid horizon by 100 ms in 4/36 scene/speed combinations; 13 cold and 87 renewed packets pass conditional geometry. All renewal outputs match the reference byte for byte, but **zero meet the measured age/stop budget**, and actual CARLA trajectories contradict several supplied actuator bounds. The contribution remains a conditional algorithm prototype, without evidence-guided driving or validated physical contracts. See the [policy report](research/policy_evidence_result_20261001.md), [reproduction](experiments/policy_evidence_20261001/README.md), and [source-backed validation](results/policy_evidence_20261001/validation.json).

**Previous integration gate: whole-body occupancy and complete stopping.** The 0.5 m disk results do not transfer directly to a vehicle. On sheng, 432 cold geometry checks and 1,044 current-ray renewals expose two contract gaps (incompatible acceleration/braking bounds and unverified initial-free assertions). Both have explicit receiver checks now, including integer expiry handling. Forty-five full-body renewal packets pass geometry, but **zero pass the complete stopping budget**. These are saved-data diagnostics, not new driving runs. See the [full-body report](research/body_evidence_result_20261001.md) and [reproduction](experiments/body_evidence_20261001/README.md).

**Previous: independently recomputable raw-ray proofs and new dynamic scans.** Version 2 lets the receiver reconstruct projection, quantization and per-ray age bounds from selected current first-return rays. Two exact optimizations match all 1,392 reference renewal outcomes byte for byte; the latest meets the modeled timing budget in 288 cases (299 geometrically valid). Two new 128-frame moving-obstacle CARLA monitor runs yield 23/1 and 22/9 geometric/timely acceptances. Both positive and negative results are retained: cold initialization and live timing remain limitations. These are receiver monitors for a 0.5 m query disk, without an ego controller or physical calibration. See the [new report](research/ray_proof_v2_result_20261001.md), [reproduction](experiments/ray_proof_v2_20261001/README.md), and [validation](results/ray_proof_v2_20261001/analysis.json).

**Previous follow-up: ray uncertainty and timing.** Supplied XYZ/pose/query error boxes and individual ray ages now produce explicit exclusion bounds. A matched best-uniform-error baseline explains equal positive-certificate counts in the 2 mm model; per-ray bounds lengthen expiry in 10/96 joint configurations, by up to 238 ms. Exact local search matches all 288 full-grid outputs. Larger-error tests retain failures: 20 mm input boxes with a 50 ms hypothetical scan give no joint certificates. These use saved static geometry and hypothetical ray times, not newly measured dynamic scans; the proof format is now implemented in the follow-up above; driving integration remains unfinished. See the [uncertainty report](research/visibility_uncertainty_result_20261001.md) and [project completion ledger](research/PROJECT_STATUS.md).

**Earlier sheng implementation: evidence validity from incomplete observations.** Actual empty-ray witnesses exclude impossible obstacle centers under explicit size/error/motion bounds; a receiver verifies a quantized geometric proof and every required obstacle class. Fresh-ray support renewal avoids rebuilding the cover each frame. In 2,000 analytic scenes, no center-exclusion or expiry-bound violations were detected under the stipulated model. A new 120-frame CARLA acquisition supports 38 timed two-class 200 ms proofs in dense free/far scenes; 20 eligible near-obstacle frames are rejected. Across all configurations, 38/232 renewal attempts succeed; sparse scans and missing templates remain refusals. These are conditional geometry and static timing diagnostics, not a driving safety guarantee or established MobiCom novelty. See the [first certificate report](research/visibility_certificate_result_20261001.md).

**Previous scheduling validation:** 44,000 synthetic episodes confirm that simple group refresh matches the core heterogeneous-lifetime result, and the candidate does not outperform a generic stationary scheduling reference. An 80-frame real CARLA coverage audit fails the primary complete-coverage gate in one of two views. The candidate has **not** established a new scheduling contribution. See the [earlier sheng report](research/renewal_sheng_result_20261001.md).

**The October audit overturns the earlier interpretation of the contention gain.** A simple region-covering greedy that avoids channel conflicts matches the old joint selector's progress in all six tested network configurations. In five non-ideal configurations its selections also match in the enumerated state grid. The earlier improvement over channel-unaware coverage is therefore insufficient evidence for a new semantic scheduling algorithm.

The earlier revised candidate was **renewing complementary evidence so it remains valid throughout action execution**. A finite synthetic diagnostic found a 13.40-percentage-point gain over earliest-expiry-first scheduling for heterogeneous evidence lifetimes, but no gain with uniform lifetimes. That is a small exact DP reference with known lifetimes and correct free evidence, **not a novel algorithm or a new CARLA result**. The latest work above implements the missing observation-to-validity interface instead of assuming lifetimes are known. Related work on physical validity, correlated information age, and coflows still needs to be ruled out before making originality claims.

This repository is a feasibility package, not a complete MobiCom evaluation. The earlier closed-loop CARLA study has five paired seeds, a software link model, and a controlled scene; zero recorded collisions do not establish natural-scene safety. The latest evidence-validity study includes new moving-obstacle scans and modeled message delay, with no ego driving controller.

## Start here

- [Policy-conditioned validity and actual actuator counterexamples (中文)](research/policy_evidence_result_20261001.md)
- [Policy code, frozen protocols and sheng reproduction](experiments/policy_evidence_20261001/README.md)
- [Whole-body, braking and history-trust integration result (中文)](research/body_evidence_result_20261001.md)
- [Raw-ray proof, exact renewal optimization and live dynamic checks (中文)](research/ray_proof_v2_result_20261001.md)
- [Version-two code and complete reproduction](experiments/ray_proof_v2_20261001/README.md)
- [Ray error/time propagation and matched algorithm comparison (中文)](research/visibility_uncertainty_result_20261001.md)
- [Full project completion ledger and remaining integration](research/PROJECT_STATUS.md)
- [Incomplete observations → conditional expiry: first certificate report (中文)](research/visibility_certificate_result_20261001.md)
- [Evidence certificate code, contract, and reproduction](experiments/visibility_certificate_20261001/README.md)
- [Source, raw frame, and receiver-proof validation](results/visibility_certificate_20261001/analysis.json)
- [Previous scheduling results and research verdict (中文)](research/renewal_sheng_result_20261001.md)
- [sheng finite validation code and reproduction](experiments/renewal_sheng_20261001/README.md)

- [Latest research judgment and finite validation plan (中文)](research/update_20261001.md)
- [New literature, reading scope, and unresolved sources](research/literature_update_20261001.md)
- [October audit and diagnostic reproduction](experiments/research_update_20261001/README.md)
- [18,000-episode baseline audit](results/research_update_20261001/baseline_audit/paired_comparisons.csv)
- [3,200-episode validity diagnostic](results/research_update_20261001/validity_probe/paired_comparisons.csv)
- [Full experiment report](research/full_experiment_result_20260926.md)
- [Frozen protocol](experiments/carla_v2x_full/PROTOCOL.md)
- [Reproduction instructions](experiments/carla_v2x_full/README.md)
- [CARLA validation](results/carla_v2x_full/carla_main140/analysis/validation.json)
- [Mechanism verdict](results/carla_v2x_full/mechanism_v2/analysis/verdict.json)
- [Semantic-noise robustness analysis](results/carla_v2x_full/robustness/analysis.json)

Downloaded literature PDFs and extracted full text are intentionally excluded. The reading log and research synthesis remain under `research/`.

![Per-ray versus best uniform error bounds under hypothetical scan timing](results/visibility_uncertainty_20261001/comparison.png)
