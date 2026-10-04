# Preserved matched diagnostic import failure

The original pre-held-out `matched.py` failed before writing matched_sheng.json:
its inherited runtime prepends older experiment paths, so `from summarize import
stats` imported an unrelated historical summarizer. Original source and
matched_sheng.log are preserved unchanged. `matched_complete.py` loads the same
local summarize.py by explicit path, verifies the supplementary freeze and records
that freeze hash; comparison loops/formulas/data/thresholds are unchanged. No
recapture or tuning. The corrected source is frozen before its first successful
matched output. This does not change the already completed certificate or physical
trajectories. The test's practically zero progress is a real negative outcome,
not an import error or a useful-driving success.
