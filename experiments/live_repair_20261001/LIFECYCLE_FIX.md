# First-tick actor registration correction

The initial capture aborted at the first vehicle tick: CARLA creates the actor
before its ID appears in `world.get_snapshot()`. The new pre-tick local gate
attempted to read that missing snapshot. Preserve the incomplete output, root
clouds/packets, log and cleanup as an implementation-failed attempt. It is not a
completed negative experimental run and is not merged with the fresh batch.

Before a corrected fresh batch, change only this lifecycle handling. When a
newly created actor is not yet registered in the current world snapshot, assert
that driving is disabled and no commitment exists, apply full brake, and advance
the SAME first acquisition tick. Record `before=null, registration_tick=true`
and its actual post-tick state. Do not add, omit or skip a physics tick. Every
subsequent tick requires a real prior snapshot. All experiment parameters and
ordering stay frozen. The original source remains `capture.py`; the corrected
entry point is separately hashed `capture_v2.py`.

Preflight after the aborted attempt found one vehicle and one collision sensor.
The original `is_alive` snapshot guard could miss a not-yet-registered actor.
The owned server was therefore stopped before any corrected capture. The
corrected cleanup destroys known owned handles directly, without that guard.
The intermediate corrected launch stopped in preflight and ran no capture.

A pre-run boundary audit also aligns sender prior selection with the existing
receiver integer deadline: ceil(observation * 1e6) must be strictly below the
registered parent's expiry. A float observation just below expiry can round to
expiry in the wire format; that prior must be omitted, not used or cause a
packing exception. This stricter guard applies to both methods. No live
corrected-batch outcome was observed before these fixes were frozen.
