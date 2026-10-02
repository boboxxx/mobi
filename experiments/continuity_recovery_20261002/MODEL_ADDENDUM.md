# Pre-benchmark age/future correction

Derivation exposed an ambiguity in frozen projection documentation: speed is
specified at observation timestamps, but independently adding age and future
travel with the same speed drops acceleration*age*future. An intermediate
prototype considered a stronger global-speed premise; it was REPLACED before
benchmark measurements, rather than narrowing the experiment for an easy pass.
No frozen old implementation/result is edited.

New typed version: observation-speed-age-v1. At each selected observation time,
Profile.speed bounds ALL members of that class; acceleration bounds subsequent
velocity change. These are upstream conditions, not measured hidden speeds.
Let d be the age of the NEWEST actual selected observation. Speed at reference
is bounded by v+a*d. Keep each ray's own age for current center exclusions, and
compute future required tiles with v+a*d. For a single observation of age d:

    v*d + a*d²/2 + (v+a*d)*h + a*h²/2 = v*(d+h) + a*(d+h)²/2.

The true selected source timestamp supplies d, never generation or receipt.
Newer truthful observations impose additional common class-speed constraints;
older rays still pay their individual position/motion errors. The clock margin
is included in future h. The newest timestamp is usable only with this explicit
common class bound: we do not infer unseen speed from an empty ray, or reset
an initial speed bound known only at the first root.

Before a legacy accepted packet becomes an anchor, the NEW receiver revalidates
its entire accepted prefix with the corrected future envelope and only already
revalidated, strictly unexpired parents. A failed parent cannot seed an anchor.
This setup work is measured separately; recovery uses receiver-owned facts.
Legacy action expiry, raw decoder/physical metadata/error/ray caps stay frozen.

Objects persist continuously: no teleportation/birth inside the proved region.
This is also implicit in historical renewal, now explicit. Neither this model
correction nor retrospective recovery establishes physical contracts or control.
