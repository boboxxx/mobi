# Causal deadline-aware repair follow-up

Declared after inspecting the fixed-budget outcomes, before executing this policy.
This is retrospective method development on the same36 tasks, not a new test set.
Keep every previous model, message and score assumption unchanged.

At current-message verification completion, stop if the certified lower horizon
already leaves at least5ms after source creation, current encoding, modeled20Mbps
wire,20ms propagation,20ms clock and200ms action reserve. Otherwise repair in the
same deterministic order as the fixed-budget algorithm. At every visit boundary,
stop on5ms remaining lower-bound slack; stop without a grant if even the upper
horizon cannot cover elapsed costs. Hard limit4096 visits. Every receiver and
policy cost is included; final actual modeled slack is rechecked after returning,
so crossing a deadline during a check cannot authorize an expired result.

Five milliseconds is a declared return-overhead margin, not a WCET guarantee.
Source creation uses the existing worst-of-five saved measurement. Each of the
three new trials encodes and measures its own current message and receiver time.
Retain all108 individual trials/trees, including timing-dependent stopping and
failures. Baseline receiver time is measured before repair in the same trial.
Do not choose the best observed trial or use future improvement to decide stop.
Independent audits validate every resulting prefix, all new bound computations,
complete partitions, any witnesses and final cost arithmetic.
