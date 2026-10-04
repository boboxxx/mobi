# Preserve the second analysis interface failure

The explicit auditor import succeeded, but the original analysis called horizon
through runtime although that wrapper exports only Evidence and decision from the
frozen query kernel. The corrected-import attempt consequently failed at its first
source query, without a completed analysis JSON. The second failure log is retained.

analyze_complete.py imports horizon directly from the already-frozen query kernel
and replaces the two R.horizon calls. This is exactly the same integer algorithm;
no equation, threshold, source observation or comparison rule changes. Both earlier
scripts remain unchanged. analysis_freeze.json pins this final interface correction
and both preserved failure logs before its first complete run. No recapture.
