# Conditional argument and boundaries

For a finite hidden Markov model m fixed for a rollout, source prior pi_m and
sensor likelihood L_m(o|x), Bayes' rule gives b_m(x|o). Delay propagates this
posterior using P_m to b_m P_m^a. Let D_u(k) be the diagonal mask of non-conflict
states for the given action's kth occupancy. For a fixed action of H steps,

    r_m(o,a,u) = 1 - b_m P_m^a D_u(0) P_m D_u(1) ... P_m D_u(H) 1.

The killed-chain product retains temporal dependence and counts the union of
conflicts across all H+1 occupancies. Endpoint probability undercounts that
union; summing marginal conflict probabilities upper-bounds it but can count
the same conflict repeatedly. These are established probability operations,
not new theorems. In the implementation D_u is fixed, allowing an independent
absorbing-state forward auditor.

For declared family M containing the true fixed model, R=max_m r_m bounds its
conditional risk given o. Each model must condition on the same observation
with its own likelihood: averaging model parameters or selecting the most
favorable posterior does not provide this guarantee. This finite family is
assumed, not statistically learned, and need not contain real traffic.

Valid start ages are V={a:R(o,a,u)<=alpha}. Encoding V as disjoint intervals
or a bitset is lossless decision serialization on this exact discrete grid.
The longest prefix from source age zero is a subset of V. V need not be
connected: a moving object may cross and leave before a later requested action.
Safe intervals already exist in SIPP and subsequent probabilistic planners;
neither interval existence nor run-length encoding is an originality claim.

The receiver uses a=(now+fee-source)/tick and never changes source. Its action
length is already included in r_m; adding H again to a would double-charge the
action horizon. Unexpected context, off-grid ages, inconsistent packets or
out-of-horizon queries refuse. This is a finite interface demonstration, not
protection against unauthenticated sensors or incorrect source clocks.

Per-action conditional risk is not whole-episode risk. For multiple causal
actions, one needs a simultaneous event bound or conditional budgets summing
to the whole-episode budget. Selection also requires a model valid conditional
on the actual runtime history. A source-snapshot posterior cannot authorize
arbitrary later decisions informed by unmodeled observations, model selection,
or trajectory changes. No guarantee is claimed after such changes.

The scientific question still missing for a journal is how to obtain a narrow,
adequate model/observation family from incomplete sensor data, then preserve
its risk bound after communication costs and receiver selection. This
reference does not solve that learning/calibration problem. It diagnoses
which representation and timing mechanisms are worth testing and which
apparent gains merely take more risk.
