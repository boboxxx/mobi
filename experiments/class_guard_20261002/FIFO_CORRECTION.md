# Root transmission occupancy correction

Post-study model audit found that bench.py charges root delivery to the initial
receiver clock but initializes source/link FIFO availability to zero. On the
slow0.5Mbps link this allows an update to start on a link still occupied by the
root. All90 first-update slow conditions have this defect (maximum overlap
298.178ms). It is a queue-model error, not a new physical observation or a
geometric theorem change. The earlier independent audit reproduced the same
initialization and therefore did not catch this modeling omission.

Retain study/analysis.json and all recorded CPU services/packets/proofs. The
authoritative timing comparison is fifo_corrected.json, produced by replay_fifo.py:
initialize sender availability to root assembly completion and link availability
to root transmission completion, then replay every serialized service. Every
mathematical result, input, method, measured duration, wire byte and drop remains
unchanged. Source ordering and receiver-reference checks still hold; these
algorithms have no arrival-dependent geometric branch. This is a deterministic
correction of a modeled link, not a second set of CPU measurements.

The corrected audit independently checks the new queues, unchanged non-timing
fields, actual packet reconstruction and all geometric/authority invariants.
Three unit tests cover root link occupancy, root source work and an idle link.
402 rows change, exclusively in the slow preset. Standard and blackout results
are byte-identical at the row/coverage level. Main report, figures and tables
must use the corrected study. The initial audit source/output is retained under
initial_cost_model for provenance, not as approval of the incorrect model.
