# Prospective component expiry qualification

Read PROTOCOL.md for the fixed law, calibration budget, selected-query certificate,
assumptions and finite execution. This experiment follows the independently audited
component development result, preserving the model, observable guard and geometry.
It does not claim unknown actors, arbitrary traffic, radio deployment or ego control.

Stages are enforced: capture once;260 independent calibration episodes/class;
600 IID mixed-class policy-certification episodes; frozen certificate;60 test
 episodes/class. Empty and failed captures refuse. No repairs or repeated data run.
All scores and policies were chosen on older development data. No new test outcome
can alter them. Initialization/function/deadline fees are measured three times from
actual XYZ/frontend/predictor/packets, without semantic label inputs to runtime.

From the repository root, restore parent logical inputs and build geometry:

```sh
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s experiments/prospective_component_20261004 -p 'test_*.py'
```

The fixture test runs three OLD development inputs through the actual source
frontend, packets, receiver and17280 replay traces, without a CARLA server or new
qualification. Outputs are temporary and deleted. An initial pre-freeze fixture
imported the older same-named producer; its failure log is retained and the fixture
now imports the new producer by exact path. No new data existed then.

On sheng, start_carla.ps1 refuses any existing CARLA process. run_capture.sh checks
the immutable source closure and stops ONLY its owned matching process afterwards.
run_evaluation.sh executes each stage in order and refuses to overwrite outputs.
To reconstruct the published result rather than collect new data, use audit.py
with --out followed by package verification. Reproduction must use the archived
raw clouds and measured fees; rerunning timings does not recreate identical fees.
No recurring automation or indefinite research loop is created.
