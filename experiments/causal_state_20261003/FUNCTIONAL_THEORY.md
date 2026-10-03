# Calibrate expiry overstatement rather than full-state uncertainty

Let F be this fixed finite family of source/view/task pairs in a complete episode.
H_f(X_f) is any fixed current-observation expiry predictor. G_f(Y) is the last
safe integer age with respect to the specified future occupancy snapshot grid.
Refused f has no authorization. Define the integer nonnegative episode score

    Z = max_(available f in F) (H_f(X_f) - G_f(Y))_+.
    delta = max_(i=1..95) Z_i.
    L_f = max(-1, H_f - delta).

If Z<=delta, every nonempty authority interval [0,L_f] ends before each relevant
unsafe snapshot. Consequently every delivered-prefix grant with original source
age plus220ms no greater than L_f is snapshot-safe. Choosing/reusing the longest
DELIVERED deadline cannot break this episode-wise statement. It does not need
independence between views, queries or time ticks. Its risk is episode-any
unconditional; the probability of failure conditioned on receiving a grant can
be much larger and is not established here.

For a fixed predictor/protocol and iid complete calibration/new episodes,
P_calibration[P_new(Z>delta)>.05]<=.95^95. Union bound over six class registries
provides joint confidence>=1-6*.95^95. This is standard order-statistic risk
calibration applied to a task functional, not a new conformal theorem. The
existing posthoc reused test comparison does not validate the iid/fixed-predictor
assumptions. Future work needs a new frozen prospective holdout before stronger
claims. Source timestamps, known class/body and task coordinates are contractual.

Among CONSTANT nonnegative additive corrections that cover ALL95 calibration
scores, max95 is the smallest one. That limited statement does not make the
predictor or deployed lifetime globally optimal, nor bound unseen future slack.
On test data we explicitly report L>G failures and (G-L)_+ conservatism. A
perfect-future-label G oracle supplies a diagnostic upper reference on the same
paid arrivals; it cannot be recovered from incomplete observations in general.
Two indistinguishable observations may have different future contacts, so an
unconditional claim of both zero failure and arbitrarily small slack is unjustified.

The fixed base H uses ALL quantized current centers,8mm radius, known enclosing
body and3m/s linear expansion, capped500ms. A separate Decimal integer contact
implementation audits H exactly. Calibration inspects true future grid contacts;
runtime only decodes received XYZ-derived centers and applies a pinned delta.
Every future grid position, not merely the interval endpoint, enters G. Continuous
inter-tick motion, unseen actors, authenticators, changing queries, arbitrary
class/sensor laws and interactive control are outside this finite contract.
