# From incomplete XYZ to conditional evidence expiry

This study replaces the old ray-penetration inverse model. It does not prove a
more accurate inversion of that model or near-optimal expiry given full raw data.
Known class, body extents, sensor transform and road basis remain assumptions.

## Calibrated state uncertainty

Fix a class and the pre-capture detector. For view v it outputs all component
midpoints C_v(X). Let A(X) mean both required views exist and have proposals.
For episode truth centers y_v define

    s(X,y) = max_v min_{c in C_v(X)} ||y_v-c||, if A(X);
             0, otherwise.

For an unavailable episode output the full center plane and refuse the task.
For an available episode output S_v = union_c B(c,q), where q is the 38th ordered
score among 39 calibration episodes. Under exchangeability of complete episodes,
with this detector and sampling law fixed independently of calibration and test,
standard split conformal gives P(all v: y_v in S_v) >= 38/40 = .95. Ties can make
coverage more conservative. Refusal is observable and includes spawn failures;
a wrong nonempty proposal set is a genuine possible coverage failure.

This probability averages over calibration and test episodes, separately for
each class. It is neither a 95%-confidence statement that a fixed deployed fit
has <=5% risk, nor coverage conditional on availability. It gives no unknown-map,
unknown-class, time-uniform, trajectory or adaptive-stream guarantee. Missing
truth in a failed spawn is not a successful perception; the declared full-plane
refusal has zero authority. The test denominator keeps such scheduled episodes.

Quantize each c to nearest centimeter. Its displacement is <=sqrt(2)*5mm.
Inflating q by 8mm and rounding outward to micrometers contains the unquantized
union. The packet transmits every quantized center and pins the radius, class,
source frame/time, calibration and contract hashes. Integrity SHA is not
cryptographic sender authentication. Class/contract knowledge is not inferred
from the point cloud.

## Conditional optimal horizon for the declared disc model

Let each candidate center be c_j, calibrated radius r, known enclosing body
radius b, fixed task center z and task radius R. Define

    g = min_j ||c_j-z|| - (r+b+R).
    D(t) = v*t + .5*a*t^2, v=5m/s, a=3m/s^2.

If g<=0 no positive horizon follows. Otherwise first contact is

    h = (sqrt(v^2+2*a*g)-v)/a,

capped at 500ms. The union's closest member determines first possible contact;
all headings allowed by the displacement-disc model are possible. This is exact
for that model, not a claim that its worst motion or body disc is physically
attainable. Integer/rational inequality checks return the last strictly safe
microsecond L and the next unsafe microsecond U; U-L<=1us, with separate cap and
already-unsafe cases. Refusal returns an unresolved [0,500ms], never a tight zero
certificate. The independent auditor uses 80-digit Decimal analytic roots plus
integer boundary checks, not the producer's solver.

On center coverage and the assumed body/motion contract, no modeled contact
occurs through L. Charge observed acquisition/callback time, conservative maxima
of measured full processing (including XYZ assembly), 20Mbps modeled wire and
240ms fixed propagation/clock/action reserve. The reported modeled remainder is
max(0,L-ceil(cost)). Timing repeats are not WCET or a real link measurement.
The initial start-only truth diagnostic was insufficient to audit the full
interval; check_expiry.py separately checks its end L. Monotonic D makes that
end check sufficient within this model, without changing any result or radius.

The <=1us bracket controls numerical conservatism ONLY after S_v and the body/
motion model have been fixed. It does not bound the loss caused by calibration,
spurious components, enclosing bodies, incomplete observations or compression
relative to full physical evidence. Distinguishing these losses is essential.

## Causality and scope

A(X) presently uses both completed sequential static views. The experiment
freezes the actor between views, and does not account for their entire holding
schedule as an online sensor family. Thus a positive modeled remainder is an
algorithmic feasibility measurement, not a causal live authorization. A receiver
cannot deploy these numbers before both required observations and their current
ages are known. No complete scene inventory or closed-loop controller is tested.

The fresh data have 17/360 excluded test episodes, despite the nominal marginal
95% construction. Each class's fixed-fit one-sided 95% risk upper bound is
10.12%–16.73%, so <=5% deployment risk is unestablished. Of 705 positive query
outcomes, 40 occur in episodes with an exclusion in at least one view; this is
not the same as 40 failing view/query horizons. Posthoc true-center disc reach
finds zero start or end violations on this finite set. That observation does
not negate the exclusions, validate physical safety, or create 705 independent
risk samples.

## Prior work and novelty boundary

The coverage construction uses ordinary split conformal prediction and its
marginal, not conditional, guarantee: Angelopoulos and Bates, sections1 and3 of
[A Gentle Introduction](https://arxiv.org/html/2107.07511v6). Its score controls
usefulness; mathematical coverage alone is insufficient.

Yang and Pavone's CVPR2023 [Object Pose Estimation with Statistical Guarantees](https://arxiv.org/html/2303.12246),
sections3–5, already uses maximum keypoint scores, geometric prediction regions
and propagation to a pose uncertainty set. Its Proposition2 also explains why a
monotone score transform alone cannot shrink the same conformal set. Our XYZ
center frontend is not a reproduction of their RGB/keypoint method; no empirical
superiority over it is established. Calibration followed by geometry is not a
new contribution. The research direction still needs a distinct communication/
causal-expiry algorithm, strong same-information baselines and dynamic evidence.
