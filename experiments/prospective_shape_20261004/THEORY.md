# Direct membership calibration avoids an unverified orientation premise

Fix the entire XYZ frontend and family of state-set predictors S_pose(X,delta)
and S_body(X,delta) using development data before this batch. Their geometry
may encode a shape prior that is physically false. This does NOT by itself
prove containment. Define score s_pose(X,c)=inf{integer delta>=0:c belongs to
S_pose(X,delta)}, and similarly s_body. Each support expands monotonically in
delta. Pose rectangles always expand eventually, and body discs similarly.
All quantized group points and all registered yaw cells are retained. Missing
input is a refusal with full-plane/no authority, so its score can be zero.

For a whole episode Z with six source observations/centers, define
S(Z)=max_sources max(s_pose,s_body). Then S(Z)<=delta implies EVERY issued
source set in BOTH families contains its actual center. No uprightness or
group-purity inference is needed for this implication: it is the definition
of directly scored membership. Priors affect efficiency, not the statistical
logic. Catalog/world/missing-output semantics and a fixed score remain vital.
The experiment assumes a known single actor/class; unseen-object completeness
does not follow from center coverage for that actor.

Let95 calibration episodes be iid under the same fixed law as a new episode,
and delta be their maximum score. For any epsilon=.05, if the fitted exclusion
risk p(delta)=P(S(Z)>delta) exceeds epsilon, ALL calibration scores fell below
the distribution's upper-epsilon tail. This event has probability at most
(1-epsilon)^95, with ties only making the bound conservative. A union bound
over six classes gives calibration confidence at least1-6*.95^95=0.954091...
for ALL class episode-any center risks<=5%. Independence between classes or
between model outputs is unnecessary; iid complete episodes within each class
is an assumption, not a property proved by selecting different seed numbers.

This is a tolerance/PAC statement about calibration draws. It is not a
95% confidence bound inferred from0/60 test failures. With0/60, single-class
one-sided95% binomial upper bound is1-.05^(1/60)=4.8703%; simultaneous six-class
Bonferroni bounds use alpha=.05/6 and are looser. Report nonzero failures using
exact binomial inversion. Do not treat six frames or repeated queries as
independent trials, or condition the above claim on acceptance/availability.
Natural-scene distribution changes, adaptive control and unknown inventory
can invalidate the experimental law.

On the joint current-center event, and separately given the BODY-DISC and
future-displacement contracts, each family's minimum query distance gives a
source-aged safe horizon solving d>Rbody+Rquery+5t+1.5t^2. Exact outward bounds
and strict integer horizon comparison avoid numerical overstatement. Taking
the maximum of the two certified LOWER horizons is valid; it is not an exact
joint-intersection optimum. The orientation prior is not a premise in this
conditional expiry implication once actual center membership is qualified.
Continuous motion/shape validity remains a separate premise, only checked
at saved simulation snapshots here. Calibration for centers alone cannot
prove physical safety or communicate unseen actors away.

Fresh results may falsify efficiency or observed coverage. Keep those results.
The max-rank rule is established statistical machinery, not our novelty;
see READING.md for primary papers and the prior whole-pose-set literature.
