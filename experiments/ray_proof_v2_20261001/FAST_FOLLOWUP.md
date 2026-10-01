# Post-diagnostic exact renewal optimization

Reference replay finished with 299 geometrically verified renewals and zero passes under the predeclared acquisition + CPU + 20 ms transport + 50 ms action budget. Do not hide or overwrite those results.

The optimized path encodes a shared sensor origin once rather than sorting one duplicate per ray. It caches validated immutable template geometry and performs a single support-location nearest-neighbor lookup because crossing eligibility and nominal planar positions are identical for all required classes. It still reprojects current rays and calls the same complete receiver verifier. The uniform sender still checks its own uniform sufficient condition.

Before dynamic acquisition, compare all 1,392 existing renewal trials against saved reference packet bytes, including missing templates, failures and both sender algorithms. No processing or physical constraint is removed. If any byte mismatch occurs, stop the comparison. Subsequent dynamic monitoring uses this exact optimized implementation; cold initialization remains the original implementation and its cost remains reported separately.
