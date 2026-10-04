# Joint finite safety and usefulness statement

Fix all three policies and the complete joint scene/service law before drawing
certification episodes. Within each episode, queries are dependent and are never
counted as independent samples. Under IID complete episodes, the selected safety
failure count conditional on n selections is Binomial(n,r), r=P(F|G). Each safety
lower-tail test at r=.05 usesδ=1/120. Independently of within-episode dependence,
the number of useful complete episodes among ALL180 is Binomial(180,u), where
u=P(M). Its upper-tail test at u=.25 also usesδ=1/120. Bonferroni over the six
fixed tests gives simultaneous confidence≥.95 that every jointly accepted policy
has r≤.05 AND u≥.25. No independence between the two tests is required.

These are standard exact binomial/selection constructions, not new statistical
theorems. Random scenes do not establish service IID, continuous geometry, unknown
obstacle completeness or a road/radio guarantee. The utility requirement is a
limited5cm/3s prototype criterion, not general route success or pointwise minimal
conservatism. It prevents calling an all-stationary controller useful.
