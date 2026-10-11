# Finite action-window reference diagnostic, preregistered 2026-10-11

This is an exact, synthetic, discrete-time diagnostic. It is not CARLA, a
reproduction of a cited planner, a learned observation model, or a road-safety
certificate. Earlier immutable CARLA experiments remain unchanged. No recurring
job is created. Source and parameters are frozen before this finite run.

Question: when a partial observation supports several possible states/models,
how much unsafe acceptance or unnecessary refusal comes from checking only an
action endpoint, applying a union bound, or reducing the valid-age set to a
single source-anchored prefix?

Nine hidden positions 0..8 form a crossing chain. Initial mass is
(0.4,0.3,0.2,0.1,0,0,0,0,0). Positions 4 and 5 conflict with the fixed
action `occupy_crossing`. Each step advances with p in {0.35,0.55,0.75},
otherwise stays. At position 8 it returns to position 0 with probability
r in {0,0.15}, otherwise stays. Sensor likelihood error e in {0.02,0.12}.
The 12 triples (p,r,e) are the declared fixed model family, not estimates from
data. The true model may be any one of these 12; it is fixed for the rollout.

The source observation is null with probability 0.4. Otherwise it reports one
of three coarse bins (positions 0..1, 2..3, 4..8), with probability 1-e for the
correct bin and e/2 for each wrong bin. Each model conditions its own prior on
this same observation. No true state/model is supplied to a decision method.

Enumerate all 4 observation outcomes, action lengths H in {1,2,4}, source ages
a in 0..16, and risk budgets alpha in {0.01,0.05,0.1}: 612 queries. A length H
action checks H+1 discrete occupancies, at a,...,a+H inclusive. Exact rational
arithmetic is used for all risk/admission decisions. Fees are separately modeled
as 0,1,2 ticks; arrival age is a-fee and negative arrival ages are excluded.
Ticks are 50 ms, immutable source epoch 1,000,000 us. This fees sweep is a
logical timing diagnostic, not measured CPU/radio latency.

Methods (same observation, model family, action, ages, budget):
* robust_window: maximum across model-specific conditional first-hit risks;
* robust_union: maximum across sums of marginal occupancy probabilities,
  capped at one; a sound, often more conservative comparator;
* robust_support: admits only when every compatible modeled path avoids conflict;
* robust_prefix: largest consecutive safe start-age prefix beginning at zero,
  computed from robust_window; equivalent conventional valid-until semantics;
* nominal_window: the first-hit risk for (p=.55,r=0,e=.02); intentionally ignores
  declared model ambiguity, audited against every true model;
* endpoint_only: maximum across conflict probability at a+H only, intentionally
  ignores earlier action occupancy;
* full_curve: same decision as robust_window with the full exact risk curve;
  strong representation comparator. No advantage over it is hypothesized.

Output every exact model-specific risk and each decision. Report acceptance
counts, largest true-model risk among admitted queries, number of risk-budget
violations, and safe opportunities lost relative to robust_window. Query counts
are not independent episodes and are not statistical sample sizes. No fitted
threshold, calibration confidence or real-traffic distribution is asserted.

Encode the exact valid-age set both as disjoint intervals and as a bitmap;
include identical timestamp, tick, action length, risk budget, horizon and
32-byte context digest. Compare real serialized bytes and exhaustive decoder
decision equivalence. A smaller bitmap is a valid negative result for interval
compression. Neither digest supplies sensor authenticity or model adequacy.

Verification: independent forward absorbing-state dynamic program for every
query/model; exhaustive path enumeration on a smaller chain; malformed packet
tests; timing fees shift admission without renewing the source epoch; exact
local/sheng scientific JSON equality. Runtime measured separately, no WCET
claim. Retain test failures and diagnostics; any scientific change needs a new
unit, not edits after freeze.

Go/no-go: this diagnostic supports only feasibility of a source-stamped
action-window interface. Journal claims require fresh moving-target closed-loop
experiments, empirically calibrated model/observation uncertainty, matched
closed-loop baselines, whole-episode risk/utility and actual transport accounting.
