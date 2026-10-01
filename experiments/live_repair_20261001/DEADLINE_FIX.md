# Post-analysis strict availability/startup correction

The eight archived runs used capture_v2.py. Three successful root-ready flags
reserve less than one encoded next sample; the fourth keeps valid history but
a later warm result has less than one microsecond left. A float comparison can
expose that result although ceil(arrival_us) reaches its integer expiry.

capture_v3.py changes only availability and root readiness: exact upward integer
arrival conversion, strict expiry, and 50,001 us next-step reservation (the
recorded CARLA 50 ms step is slightly above .05). Actual child reference is still
checked separately. The next-step bound is a simulation configuration assumption,
not a wall-clock guarantee. No expiry, raw-ray error or maneuver bound is enlarged.
The original capture sources and observations are preserved. This entry has unit
and archived-deadline audits only; it has NOT produced a new CARLA driving batch.
