# Statistical guarantees and limits checked before fresh evaluation

**Vovk, Conditional Validity of Inductive Conformal Predictors (ACML2012).**
[Full primary PDF](https://proceedings.mlr.press/v25/vovk12/vovk12.pdf), introduction,
sections2–5 and propositions2a/2b. It distinguishes marginal, training-conditional,
label-conditional and object-conditional validity and relates PAC guarantees
to classical tolerance regions. A held fixed calibration can be qualified with
two separate error/confidence parameters; that is not pointwise deployment
coverage. Our max95/union-bound calculation is this established machinery.

**Bian and Barber, Training-conditional coverage for distribution-free predictive
inference.** [Full author PDF](https://arxiv.org/pdf/2205.03647), definitions of
conditional coverage and split-conformal guarantees. It distinguishes validity
of a deployed fitted rule from an average over fitting/calibration randomness.
Do not substitute the stronger claim for a marginal conformal statement or
condition on the receiver's accepted decisions without a selection guarantee.

The fixed complete-yaw predictor came from the development study
pose_support_20261004. Its READING.md records full readings of AlignNet-3D,
Yang/Pavone's certified pose-set work, adaptive two-step box uncertainty and
Proof-of-Perception. Statistical set coverage and geometric propagation are
prior art. The present batch assesses the missing fresh qualification, not
a new conformal theorem or mobile/wireless selector.
