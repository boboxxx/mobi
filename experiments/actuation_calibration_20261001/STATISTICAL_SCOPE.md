# What this calibration can and cannot establish

The two predictors are fixed using only 100 training episodes. Their features
are available before the candidate command: current speed, its square, previous
sampled acceleration, whether the actual gear is first, next throttle/brake,
and the fixed relay target. A constant-mean predictor is the matched baseline.
No calibration or test outcome enters the least-squares fit.

For episode z, Y(z) is a four-vector: complete sampled forward/rear/lateral body
extension and the start of a speed band that persists through the rest of the
recorded two-second backup. The final body bounds use all eight 3D corners,
including pitch, roll, yaw and the box's local offset/rotation, projected into the
reference horizontal frame. The preliminary yaw-only corpus is excluded under
POSE_ADDENDUM.md. Define a joint score for fixed predictor f:

    s(z) = max(0, max_j (Y_j(z) - f_j(z)) / scale_j),

where the three distance scales are 0.1 m and the time scale is 0.1 s. One score
is computed per complete episode, not per frame. Failure to observe a persistent
speed band or any collision gives an infinite score. No unfavorable episode is
deleted. The calibrated predictor is f(z) + q*scale, where q is the largest of
299 independent calibration scores.

For any fixed training data and predictor, assume calibration and deployment
episodes are iid from the same distribution in PROTOCOL.md. Let F be the score
CDF and alpha=0.01. For continuous scores,

    P_calibration[P_new(s_new > q) > alpha] = (1-alpha)^299.

With atoms and strict exceedance, the right side is an upper bound. Thus the
population joint exceedance probability is <=1% with calibration confidence at
least 1-.99^299 (>95%). This elementary one-sided order-statistic tolerance result
does not require Gaussian residuals. It is not a new conformal method.

The guarantee is per prespecified predictor. Applying it separately to two
predictors does not imply a simultaneous 95% statement; a union bound would give
only at least 1-2*.99^299. The state-conditioned predictor was prespecified as the
candidate and is not selected after looking at the held-out results.

The 400 independent test episodes use the frozen predictor and correction. For
k joint exceedances among n test episodes, the report gives the one-sided 95%
Clopper–Pearson upper bound Beta^{-1}(.95; k+1,n-k), with the usual n=0 and k=n
boundary handling. The same calculation is reported for the subset admitted by
the fixed counterfactual gate and for preregistered speed strata. These are
separate intervals, not a simultaneous confidence band.

Marginal 1% error alone does not guarantee 1% error among admitted states. The
gate can preferentially select difficult cases. The independent admitted-subset
audit is therefore essential; even a successful audit covers only this same
episode law and selection rule. New adaptively visited driving states can follow
a different law. The calibration cannot be reused for that change by asserting
that their speeds lie in the same numeric range.

Random requests are independently generated and every vehicle is recreated.
This supports the intended design but does not empirically prove simulator
stationarity or absence of persistent hidden state. The probability statement
remains conditional on that episode-law assumption. Three fixed spawn points,
one vehicle/controller/weather and 50 ms observations are a deliberately narrow
calibration scope. Unobserved excursions between snapshots, later post-window
motion, sensor error, hidden obstacles and communication do not receive this
probability guarantee. Physical movement authorization remains false.

Relevant prior source: [Formal Verification and Control with Conformal
Prediction, v3](https://arxiv.org/html/2409.00536v3), trajectory abstractions and
Section 20, distinguishes complete-trajectory calibration, future trajectory
coverage and deployment-distribution requirements. The present implementation
uses a classical maximum-score tolerance bound to make the calibration-sample
confidence separate from the population error probability. It does not claim
that a finite sample establishes a deterministic actuator limit.

For the classical order-statistic connection, see [Hulsman, 2022, Sections
4.2–4.3](https://arxiv.org/html/2210.14735v1): the univariate score reduction and
Beta coverage law explain the distinction between marginal coverage and
calibration-conditional tolerance statements. This is a public master's thesis,
not evidence of a new peer-reviewed contribution by this project.

The counterfactual gate also assumes its model and feature computation have
completed by the supplied decision age. Neither their wall-clock execution tail
nor actuator network latency is included in the recorded stopping-band target.
An independent execution watchdog and fresh closed-loop distribution audit are
still required before using this component in online evidence-guided driving.
