# Current-witness perturbation verification

Use the existing dense_0_free_00, v=0.5, H=0.4 packet. Cross endpoint x shifts
0/1/5/20/100 mm, per-ray ages 0/10/50/100 ms, retained fractions 1/0.9/0.5, and
original/reversed ray order: 120 fixed cases. Make the mutation in integer raw
rays, serialize with a valid checksum, and require reference JSON, incremental
JSON, full binary and incremental binary verification to agree. Measure receiver
time separately for all four, rotating order. No physical interpretation of
these synthetic ray perturbations is asserted. They exercise failure fallback,
not just identical stationary scans. No movement authorization is evaluated.
