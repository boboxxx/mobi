# Causal per-frame validity with fixed-calibration tolerance coverage

The XYZ frontend is fixed before all new episode draws. In a captured episode,
each current frame independently returns the union of every proposed center
or full-plane refusal if it has none. It never waits for another frame/view.
Calibration can inspect complete trajectories offline; runtime cannot.

## A finite-family risk statement about the fixed calibration result

For class c, let episode score Z be the largest center residual over its six
scheduled scan frames, treating each refused/missing frame as full-plane with
no authority (residual0). A wrong nonempty set has its actual error. Let
q_c=max(Z_1,...,Z_95) over iid calibration episodes. Define fixed-fit risk
p_c(q)=P(new episode has ANY non-refused scan with residual>q).
For any score distribution, including ties/zeros,

    P_calibration[p_c(q_c) > .05] <= .95^95.

Proof: an upper5%-tail threshold partitions the score law. A maximum calibration
score falls below a threshold with tail probability greater than5% only when
all95 iid calibration draws fall below it, with probability at most.95^95.
A generalized quantile handles ties by the same weak upper bound. This is the
standard maximum-order-statistic tolerance bound, not a new conformal theorem.
By union bound over six classes, probability at least1-6*.95^95 (about95.4%)
over calibration that all six FIXED-fit episode risks are <=5%. It does not
require the six class calibration sets to be mutually independent for the union
bound, but requires iid episodes within each class under the test law.

This strengthens the earlier39-sample rank38 marginal-only statement under the
additional iid assumption. It calibrates SIX observed scan snapshots, not all
future positions, conditional non-refused frames, arbitrary deployments,
unknown inventories or indefinite streams. A high calibrated radius can still
make every useful query refuse; risk coverage does not ensure efficiency.
Test binomial upper bounds are independent descriptive evidence about the fixed
fit; they need not numerically be <=5% for the calibration tolerance theorem to
apply under its assumptions. Distribution drift or interaction with ego control
can invalidate those assumptions.

Quantize centers to1cm and outward-inflate q_c by8mm. True state membership then
propagates to the known body-disc and declared speed/acceleration envelope. The
first possible task contact is solved exactly as in the prior center-union
model, with last-safe integer microsecond L and next-unsafe U. <=1us numerical
gap bounds only model solving error, not state, body or physical model loss.

## Absolute deadlines and paid arrival

A scan with source timestamp t_s produces deadline d=t_s+L. Sender processing,
serialization, FIFO queueing,20ms modeled propagation and receiver processing
consume this fixed age budget. Arrival never changes d. At decision time now,
a grant needs d>=now+220ms for clock/action reserves. Thus no newer timestamp is
invented by packet compression, reception or reuse. A refusal creates no grant;
an older fact may remain valid only until its original deadline.

Sender jobs release at source time plus observed acquisition/callback duration.
Each method pays its own measured source and receiver durations, three repeats
with maxima and upward microsecond rounding, on independent FIFO CPU/link
queues. Link presets20Mbps/2Mbps. Simultaneous views share these queues. This is
a causal discrete-event trace model whose clock is CARLA simulation time;
measured wall durations are imported as modeled costs. It is not a live physical
link or a WCET guarantee. Future scan rows cannot alter earlier prefix decisions.

All primary decisions occur at steps0..15 (every50ms), two fixed queries per step:
32 outcomes per scheduled test episode, including failed spawns. Their220ms
clock/action endpoint lies within the step0..20 truth-snapshot horizon. Queries
and views are correlated. There is no ego driver or task-choice feedback.

The lossless-center and full-XYZ baselines reconstruct EXACTLY the same center
union with the same radius, outward protection and geometric horizons. Their
own processing/wire/queues are paid. They are strong representation baselines;
any timing or byte advantage must be measured, never assumed. A fixed200ms
source TTL truncated to the geometric horizon is a conservative diagnostic and
cannot outlast the220ms reserve; it is not a competitive SOTA comparator.

## Physical and scientific limits

Ground truth is evaluated only after message/trace outputs. Audits check captured
center motion against the envelope and bbox corners against known enclosing
radius, all observed snapshots in granted action windows, and analytic true-
center model contact at entire window end. Finite20Hz snapshots cannot prove
continuous physical sensing/motion safety. Noninteractive one-object experiments
provide no full scene inventory or causal closed-loop driving evidence.

[Lindemann et al., RA-L2023](https://arxiv.org/html/2210.10254), sections3–4, already
calibrate trajectory prediction regions and connect them to planning guarantees;
its Theorem1 uses a temporal union bound. Our change addresses frame arrival and
fixed-calibration finite-family coverage in this specific communication pipeline.
Those principles are prior art; this experiment is not proof of MobiCom novelty.
