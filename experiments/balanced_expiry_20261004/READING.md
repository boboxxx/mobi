# Rationale and primary-source limits

The concrete problem is a fallback geometric error dominating one global
normalized threshold and inflating radii on supported observations. The proposed
repair uses the existing learned residual unit on supported observations and a
known body unit on fallback, within one whole-episode score. It is a mechanism
probe, not a novel conformal construction or proved MobiCom contribution.

Frameworks used from brainstorming-research-ideas: failure analysis, component
decomposition and the simplicity test. Candidates considered: remove pose
entirely (loses useful geometry); class-specific threshold patch (test-driven
and rejected); separate supported/fallback calibration (more event/sample
accounting); observation-type units (selected finite probe); guarded ridge;
query-direction scores (restricted query domain); conditional policy testing
(needed separately); more templates (no evidence for the bottleneck); exact
intersection solver (old clip gains too small); ego-driven active sensing
(important later, not supported by this static trace). The strongest objection
is that bigger fallback sets may worsen fallback utility and normalization is
established. Report both effects and retain strong baselines.

[Papadopoulos, Vovk, Gammerman, JAIR 2011](https://arxiv.org/pdf/1401.3880),
arXiv upload 2014: read introduction and normalized-score definitions in §5,
especially equations24–32. Neighbor-distance and neighbor-label-variation
normalizers already adapt interval sizes to local difficulty. Our use of
type-dependent units does not establish conditional coverage. No replication
of their benchmark experiments or reading of every proof is claimed.

[Angelopoulos et al., Learn then Test, author v5](https://arxiv.org/html/2110.01052v5):
read formal setting§1.1, theorem1/Bonferroni§2 and selective classification§3.2,
equations7–8. The method counts errors among selected independent examples and
uses exact binomial tails for binary selective loss. Our episode certificate
uses this established principle, not a new selective-risk theorem. HTML's
internal date differs from version metadata; no venue/date inference is made.

For a frozen selector and iid full episodes Z, let G indicate any authorization
and F indicate at least one grant referring to an excluded source. Conditional
on selected sample size N, the selected labels are iid Bernoulli with parameter
P(F|G). An exact upper endpoint at δ/M, or equivalently a binomial lower-tail
test at target ε, controls false certification. Union over M fixed policies
allows selection among certified policies. N=0 certifies none; repeated queries
are not samples. Score calibration and selector fitting must be disjoint from
policy certification; fixed type or class mixing assumptions must be stated.
The certificate does not cover per-query failure probability, new locations,
new inventory or physical collision risk. Adaptive ego policies need full
policy-on-episode qualification, not reweighting these static traces.

Future independent execution needs separate score calibration, policy
certification and test stages, with all models/fees/selection rules fixed before
certificate data. Choosing new thresholds after reading certificate failures
requires simultaneous testing of an independently fixed candidate family, not
an uncorrected retry. This turn does not claim that such fresh data exist.
