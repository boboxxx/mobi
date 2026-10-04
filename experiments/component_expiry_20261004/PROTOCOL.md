# Separate component development, frozen before execution

Two fixed families component_mean/component_modes. Supported score, set and
inference remain exactly local_mean/local_modes: pose residual/10mm plus learned
center residual/σ; cheap maximum of distances. Only supported frames contribute
to the respective supported entire-episode maximum. Other frames contribute0.
Fallback uses a SHARED whole-episode maximum of the larger body/pose violation
in μm; supported and empty frames contribute0. The maximum fallback calibration
value is used directly as geometric slack for the joint body/pose set. Runtime
selects using the frozen predictor's observable support guard; no truth input.
Empty observation always refuses. Bodies, motion, source epoch, model, queries,
features and guard remain fixed. No data-dependent union selector is introduced.

Development uses the complete already examined 1110-episode parent corpus.
The 125 calibration-labelled episodes/class are now only development partitions.
Report all60 planned test-labelled episodes/class including failures, exclusions,
age overstatements and worse source queries. No prospective certificate follows
from this post-test probe.

For a genuinely new IID whole-episode calibration stage, each component has
marginal full-episode exclusion target2.5%. Maximum over n independent episodes
has bad-calibration probability at most(0.975)^n. For six classes, two supported
families and ONE shared fallback there are18 calibration events. Their joint
error probability is at most18(0.975)^n. n260/class is sufficient to spend at most
0.025 on calibration confidence. A family's episode exclusion is contained in
the union of its supported and shared fallback events, giving marginal risk5%.
These are full-episode events, not coverage conditional on observed support.
Previously rejected candidates are historical controls, not deployed candidates.
Any added calibrated baseline must receive its own confidence budget.

P(error) does not control P(error | grant). The next fresh policy-certification
stage must freeze the service/query policy, select one query independently per
IID episode, and use exact-binomial LTT with multiple-testing adjustment for
both exclusion and source-age/action failure. Failed certification refuses the
policy. Old test data cannot certify this candidate. This is standard risk
accounting, not a claimed new conformal theorem or MobiCom novelty.
