# Prediction uncertainty, rather than an assumed physical speed bound

For a current source frame s, retain its entire XYZ candidate center set C_s.
For future snapshot index j=s,...,s+10, at50ms spacing, define

    Z_sj = max(0, min_c ||y_j-c|| - 3*(j-s)*.05).
    Z_episode = max over every available source/view/future pair Z_sj.

A missing/refused source predicts no authorized state; it has full-plane refusal.
There are up to66 pairs per captured episode, depending on frame availability.
The max of95 iid calibration EPISODE scores yields the same maximum-order-
statistic risk/confidence statement in THEORY.md. Correlation among source/view/
future pairs needs no separate independence, since the episode is the sample.
Under the stated law, probability at least1-6*.95^95 over calibration that each
of six fixed-fit episode-any future-snapshot exclusion risks is<=5%.

Radius q+3*age around every current candidate creates a union prediction tube.
The3m/s slope is a frozen design parameter; physical motion exceeding3m/s can
still be represented by a larger q. Coverage is established statistically using
future calibration positions, not by asserting a physical3m/s velocity bound.
Future test labels only score predictions; no source or receiver step reads them.

Quantization/outward inflation preserves the current centers and their future
expanded regions. A source timestamp and its geometry give an absolute last-safe
integer age. Exact linear first contact is

    h = max(0, (min_c ||c-query|| - (q+body+task_radius))/3), capped500ms.

Binary rational solving and a separate Decimal root/integer boundary audit bracket
this fixed tube model to<=1us. This says nothing about minimum statistical tube
size or optimal expiry given full raw observations. Source, queue, wire and
receiver delays retain the original deadline. The paid query window extends
through NOW+220ms and uses only packets delivered by NOW.

On the event that all relevant predicted future snapshots are covered, a grant
excludes the modeled body disc from the task at those snapshots in its window.
The calibration statement covers that finite observed grid. No continuous
interpolation, arbitrary physical velocity, unseen object inventory or indefinite
stream guarantee follows. CARLA's recorded timestamps are checked against the
50ms frame grid; the20ms clock margin exceeds its observed representation drift.
The original state-set5t+1.5t² model and this statistical3t tube remain separate
outputs, with independent radii, measured processing and packet identities.

Calibrated trajectory regions are established prior work, including the RA-L2023
paper linked in READING.md. Any future submission must show a distinct algorithm
for evidence content/arrival/expiry and stronger diverse/closed-loop evaluation.
