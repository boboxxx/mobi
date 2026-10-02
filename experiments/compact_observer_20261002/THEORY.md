# Conditional equivalence and conservative computational restriction

The established position-set derivation and all upstream physical/time/object
conditions are unchanged from `../set_observer_20261002/THEORY.md`. These
optimizations make that baseline more useful in finite replay; they do not
create a new set-membership theorem or establish physical safety.

## Exact temporal dictionary

A template retains every original static payload field and ray ordering.
Only reference/sequence/horizon are placed in each step record, and each ray
timestamp is replaced by its integer age relative to that step's reference.
Reconstruction restores timestamp=reference−age and retains the original
payload checksum. Changed geometry/ages/metadata creates another template.
Every reconstructed step then gets the original checksum, shape, physical
contract, time/sequence and full geometric checks. No approximate matching or
sender-derived occupancy replaces raw evidence. Bounded decompression rejects
trailing/truncated/oversized input; dictionary/ray/expanded-bundle limits apply.

The dictionary does not authenticate data. Its valid-input equivalence is a
serialization property; full receiver acceptance is still needed. Shared
transmission optimization is supplied to fixed-K and both position baselines.

## Exact caches within one rebuild

For the fixed registered scope/motion/profiles/error model of one rebuild,
decoded origins, endpoints and relative ages determine projection and whole
tile empty masks. Keys use the exact integer arrays, not rounded floating
similarity. Fixed-K full collar checks additionally depend on sent horizon.
Temporal/sequence/contract checks remain mandatory on every actual raw step.

The positional transition depends on the entire predecessor possible mask,
the exact computed travel distance, class/grid and current exclusion geometry.
A transition cache includes all these variable inputs (class/grid is fixed
per rebuild/class); stored outputs are readonly. Caches start empty at each
target, have bounded step counts, and all misses/key construction are timed.
There is no free previous-target solver or future-state oracle.

## Unknown computational exterior

The original physical/source contract still has15m half-domain. A smaller,
aligned local square is only a computation choice. Initialization crops the
fully validated original coarse posterior, optionally lifts each parent tile
to four fine children, and removes children only with unchanged physical ray
evidence. All positions outside the crop are treated as unknown.

At every propagation, any local tile within the previous reference travel
bound of the crop boundary is marked possible, before current exclusions.
An actual center inside the window either came from a retained prior tile or
entered from its unknown exterior. Both cases are contained. A center that
leaves and re-enters is covered by the same continuous displacement bound.
Future acceptance also requires its whole query envelope inside the window.
Thus the crop can add conservatism, but cannot create free-space knowledge.
The particular9m/11.5m windows are frozen computation parameters, not learned
physical promises; moving or different scenes may lose useful certificates.

## Established squared distance transform

Read §2.1, Algorithm1 and §2.2 of
[Felzenszwalb and Huttenlocher, Distance Transforms of Sampled Functions,
Theory of Computing2012](https://theoryofcomputing.org/articles/v008a019/v008a019.pdf).
The separable lower envelope computes exact squared Euclidean lattice distance
in linear work per dimension. `propagate.cpp` implements that established
method, skipping absent sites; it does not claim a novel transform. Whole-tile
distance remains the minimum of four target-corner distances to predecessor
tile vertices, as independently derived in the prior package.

The native implementation retains the outward1e−9m comparison and unknown
boundary injection, and compiles without contraction/fast-math. Unit checks
compare brute square unions and the previous EDT; the experiment auditor uses
uncached vertex KD trees and individual-ball masks. H/H+1 uses complete required
tiles rather than native cached frontier results. Conditional soundness still
depends on upstream observation/error/object/common-clock bounds.
