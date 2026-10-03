# Timing and source-freeze revisions before first evaluation

The capture detector, draws and physical procedure were never changed. Prior to
any calibration/test evaluation output, code inspection corrected three analysis
implementation details, preserving every preceding source/freeze version:

1. Compact JSON output to avoid the GitHub single-file limit for complete traces.
2. Normalize the auditor's expected empty center arrays to shape(0,2), and pin
   each record's actor ID to its episode ID. No producer changes from this fix.
3. Include np.frombuffer plus every-fourth-return .copy() inside the measured
   source interval. The capture callback timer ends before this operation, so
   omitting it would undercount online source processing.

Only every fourth original return was archived. For this memory-copy measurement,
a zero-filled buffer with the recorded original length and raw dtype is created
BEFORE timing; archived points occupy their original stride-four slots. The
inside-timer strided copy therefore selects exactly the stored observations.
Unused slots are neither observed raw evidence nor perception inputs. This
layout fixture measures sampling/copy overhead; it does not reconstruct lost
sensor returns or validate physical noise. All methods pay this operation,
XYZ assembly, their own source encoding and receiver decoding/geometry. Samples
record selection_s separately, within source_s. Three repeats, observed maxima,
not WCET. File load/logging/archive saves are excluded from the modeled online
sensor-buffer path.

The native launcher originally had a30min timeout. Actual finite930-episode
capture was projected to exceed it. extend_server.ps1 verifies the owned server
and exact own parent-launch command, suspends only that launch timer, and guards
the same server for a finite45min extension. Stop the server with stop_carla.ps1;
the guard resumes the original launcher when it exits. Receipts preserve PID,
parent PID, time and reason. This affects service lifetime, not sampling/model
rules; it is not a recurring research loop.

The functional receiver-only follow-up reuses exact primary messages and source
cost samples, and remeasures decoding/geometry/policy-registry validation three
times. Tube and functional finite jobs briefly overlapped on the shared host;
these are observed loaded-host maxima, not controlled isolated-runtime or WCET
estimates. The action-aware successor ran after both producers were terminal.
Do not attribute small representation grant differences exclusively to bytes.
