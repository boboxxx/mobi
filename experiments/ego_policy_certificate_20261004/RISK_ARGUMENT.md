# Whole-episode selective risk argument

[LTT, Section3.2](https://arxiv.org/html/2110.01052v5) controls binary risk on the
selected subset with an exact binomial tail. We use this standard construction;
it is not a new statistical theorem.

LetZ contain a complete independently drawn scene and its service/execution
behavior. Fix the controller before drawing certification episodes. G(Z) indicates
any authorization; F(Z) indicates the union of declared failures in that episode.
For IIDZ, conditional on n selected episodes, their failure count is
Binomial(n,r), where r=P(F|G). No independence between frames or queries is required.

For α=.05, compute p=Σ[j=0..k]C(n,j)α^j(1−α)^(n−j). Accept only if n>0 and
p≤1/60. Three fixed methods use Bonferroni, so with confidence≥.95 every accepted
method has r≤.05. At k=0 this requires n≥80. Capture-incomplete accepted episodes
are failures. No old calibration confidence is used; learned outputs are fixed
proposals tested directly.

The argument requires joint IID, including timing. It does not prove timing IID,
continuous motion bounds, unknown-target completeness, indefinite operation or
actual wireless/road safety. Held-out tests follow the frozen certificate.
