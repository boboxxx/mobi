# Exploratory action-eligible task-expiry calibration

This is a single successor to FUNCTIONAL_PROTOCOL.md, proposed after its
terminal producer/audit/summary showed2770 union grants versus3807 tube grants
at20Mbps and large additive corrections. No per-frame task residuals were used
to select a threshold. The fixed220ms action/clock reserve is inherited, not tuned.
Existing calibration/test are reused development; no untouched holdout claim.

All functional protocol definitions and restrictions remain except:
1. A base current XYZ-predicted contact age H<220000us creates NO authority (L=-1).
2. Calibration score takes max(0,H-G) ONLY over pairs whose H>=220000us.
3. For eligible pairs L=max(-1,H-max95score); others remain L=-1.
4. The diagnostic perfect-grid oracle obeys the SAME base eligibility filter,
   measured arrival times and paid queues. It is not an implementable baseline.

The fixed filter reads only current received centers and the required action
budget. It uses no truth, future/past view gating or favorable spawn removal.
Every grant requires source-age>=0 and L>=source-age+220000us; therefore a pair
whose H<220000 can never have produced a grant even with zero correction.
Calibrating errors on those pairs needlessly penalizes authority-capable pairs.
Risk is now episode-any unsafe action-capable deadline, with the same standard
max95 tolerance statement ONLY under a frozen-predictor/eligibility iid law.
Refusals and spawn failures remain in all denominators. Context-conditional
non-refused/granted risk and continuous physical safety are not established.

No other predictor, sampling, body, queries, message, baseline or timing changes.
Keep the unsuccessful unfiltered functional study alongside this revision.
Do not repeat tuning, recapture this law or create a recurring research loop.
