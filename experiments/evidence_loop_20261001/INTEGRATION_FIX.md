# Finite integration correction after the preserved first batch

The first four attempts never spawned a car: all roots failed. Saved-data
inspection found view 0 geometrically covered both required classes but selected
21,710 unique nearest-ray candidates, exceeding the existing 8,192-ray wire
limit. Existing coverage-preserving greedy compression produced a valid packet
in 1.7003 s (too late for direct action). View 1 actually lacked coverage.

Use existing `compress.pack` for cold support construction and existing
`renew.renew` to select and fully verify CURRENT rays thereafter. A template is
only a support hint, never a retained free assertion; expired templates cannot
supply geometry without newly reverified rays. Preserve the same three root
attempts, horizon, region, errors, obstacle profiles, controls and drop schedule.
No tuning to rescue the failed view. All cold processing cost still advances
physics before any resulting decision. Save the original batch separately.

Also fix the receiver check timestamp: source timestamps round upward to integer
microseconds, so checking at the original float timestamp may spuriously reject
a packet as future. Use the already stipulated 20 ms modeled-link check time,
then advance ALL measured delay and recheck region expiry before control. This
is not additional grace or extension of expiry. Source-provenance validation
will replay the original and corrected entry points separately.

`capture_v2.py` is the corrected, separately hashed entry point. This correction
was frozen before its fresh four-run capture. It does not supply a physical
watchdog, change the calibration law, or prove a physical sensing contract.
