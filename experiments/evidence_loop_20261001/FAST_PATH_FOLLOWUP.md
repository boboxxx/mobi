# Second finite correction: reduce duplicated computation, retain all failures

The corrected four-run batch produced valid view-0 roots but processing aged
most beyond their 400 ms lifetime. One root was technically unexpired with less
than one microsecond remaining; the next sensor tick arrived after expiry and
self-occlusion then prevented renewal. No forward command was issued. All of
that batch remains archived. It is not successful evidence-guided driving.

Before a third fresh batch, freeze these changes only:

1. Use the existing nominal ray-plane proposal calculation and exact local
   nearest-neighbor shortcut to choose current rays. Full error propagation and
   geometry validation still run on the selected rays. Compare proposals with
   the exhaustive previous renewer on all archived third-batch inputs.
2. In the receiver, perform the complete existing verifier once, then construct
   the identical derived region locally. The old history receiver verified the
   same packet twice. Retain scope, monotone sequence/time, registered prior,
   prior-expiry and integer deadline guards. Compare all outcomes and regions
   with the old strict receiver, including replay and malformed packet checks.
3. Before creating ego, require the initial proof to remain valid at least one
   more 50 ms acquisition tick. This is a stricter initialization guard.

The 400 ms horizon, geometry, sensor/obstacle assumptions, actuation model,
controller, dropout pattern and three-root-attempt limit stay unchanged. This
is a finite implementation fix, not a new research contribution or a relaxation
of the physical assumptions. The original 1% calibration guarantee does not
apply to these adaptively visited driving states.
