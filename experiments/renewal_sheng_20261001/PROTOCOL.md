# Finite renewal candidate validation on sheng

Written before the new production runs on 2026-10-01. This is an internal frozen finite protocol, not externally registered research. Existing October pilot results informed its design.

## Questions and stopping rules

1. Does the previous three-step DP advantage survive basic multi-step and group-refresh comparators using identical validity information?
2. How much does overestimating validity, delayed service, or changing required regions change the conclusion?
3. Can real CARLA sensor coverage support a free/unknown distinction before promoting the mechanism to a driving claim?

Failure is a valid outcome. No claim of novel DP/MPC, faithful reproduction of named literature algorithms, general driving safety, or completed MobiCom evaluation will be made. If sensor coverage cannot support the certificate, do not run a driving controller that treats missing returns as free.

## Mechanism suite

500 seeds, 60 communication decisions, fixed configs in run_suite.py, all listed methods. Shared exogenous outcome table indexed by seed, decision, region; no policy can inspect future draws. Future required sets are not revealed. A packet samples at transmission start and arrives after the configured integer service duration. Each method shares sensing, channel statistics, budgets, and supplied validity bounds. Overestimation is applied equally to all methods and evaluated against the same shorter true lifetimes.

Methods: EDF; normalized age; longest-lifetime-first periodic cycle; group refresh (repair invalid regions longest-lifetime-first, idle if next action is supported); deterministic three-step MPC; stochastic three-step MPC (old candidate generalized to service duration); stochastic six-step MPC (strong reference). All are transparent baselines, not claimed as literature implementations. Exact DP is restricted to 2–3 regions.

Primary metric: fraction of decision epochs with all required evidence valid through the execution guard. Also record claimed opportunities, false-valid opportunities, transmissions, bytes, and scheduling time. A claim is evaluated against true validity at the same commit instant. These are synthetic opportunities, not kilometers or collisions. All evidence is assumed correct and free; validity error is not a detector experiment. Switching requirements are known only at the current decision, while the executed action uses the set held during that decision.

Bootstrap paired differences by seed (4,000 replicates); report every configuration and comparison with group refresh, deterministic MPC3, and MPC6. No selection of favorable configurations as the sole result. Comparison among configurations is descriptive, not an independent-sample pooled inference. Fixed metadata/header bytes are a transparent model, not measured V2X overhead.

## Physical-validity unit and stress checks

Implement a conservative 1D incoming-lane reachability bound from observed empty length, position uncertainty, speed bound, acceleration bound and clock uncertainty. This assumes coverage and correct free evidence and is not new theory. Test coverage refusal, kinematic expiry, optimistic-bound violations, timestamp monotonicity and zero/negative margins. Sample a finite bounded kinematic stress set with independent seed; verify the algebraic guarantee only under its explicit bounds.

## CARLA gate

Use the existing matched 0.9.15 Windows server and sheng client if accessible. Run a finite stationary semantic-LiDAR coverage audit with free and occupied corridor configurations. Require actual ground returns in every discretized required cell and reject cells with obstacle evidence; absent coverage is unknown. Preserve frame IDs and actor cleanup. This is a sensor validation gate, not natural-scene safety certification or full MDrive evaluation. If this gate fails, record the failure and do not manufacture a successful driving experiment.

No recurring automation, endless optimization, or background research loop. New outputs use a distinct directory, old artifacts remain frozen.
