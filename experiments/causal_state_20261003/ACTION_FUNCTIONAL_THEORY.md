# Include action eligibility in the score family

Use the fixed definitions H,G in FUNCTIONAL_THEORY.md, and E_f=1[H_f>=B]
where B=220000us is the existing required action/clock reserve. Define
Z=max_(available f with E_f=1)(H_f-G_f)_+, zero if none. Delta=max95Z.
L_f=max(-1,H_f-delta) for E_f=1 and L_f=-1 otherwise.

On Z<=delta every available eligible L_f<=G_f; ineligible f cannot grant.
A source-aged causal action needs L_f>=now-source+B, with now>=source.
Thus ANY false grant implies Z>delta. Standard maximum-order tolerance control
then applies at the whole episode level under a predictor/filter frozen before
fresh iid calibration. Correlation within episodes and delivered-prefix choice
do not break the simultaneous implication. This experimental successor reuses
posthoc development data, so it supplies implementation and diagnostic evidence,
not a prospective validation of that theorem for the fitted result.

Removing ineligible score terms weakly reduces delta on identical calibration.
For eligible pairs this weakly increases geometric L relative to the unfiltered
policy. It does not guarantee greater paid grants under separately measured CPU
costs, reduced failures, or minimum conservatism relative to incomplete raw data.
The 220ms requirement is not a safety/transport upper bound; actual arrival and
compute queues are still separately charged. General different action budgets
need a correspondingly frozen calibration family; no arbitrary-query claim.

Direct task calibration and fixed-pipeline eligibility are prior methodological
ideas: see the2026 safety-clearance preprint added to READING.md. The candidate
communication contribution would require distinctly new evidence/content/expiry
selection plus strong prospective and ego-control tests; this experiment alone
does not establish MobiCom novelty.
