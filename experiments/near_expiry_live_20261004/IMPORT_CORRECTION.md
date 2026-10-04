# Preserve the first analysis failure

All18 new captures and the independent physical/geometry audit finished. The
pre-frozen analysis failed before producing its first metric: importing the generic
name audit after inherited runtime path setup resolved an unrelated body auditor,
which has no geometry function. The original analyze.py and original failure log
remain unchanged. No new capture or threshold change follows this failure.

analyze_importsafe.py differs only by resolving this experiment's audit.py via its
explicit file path and a unique module name. All comparison formulas, declared
queries, thresholds, loop order and summary statistics remain byte-identical.
The supplement freezes this exact correction and the preserved first-failure log
before running the corrected complete analysis. It is an implementation correction,
not a new scientific method or an outcome-dependent retuning.
