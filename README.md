# Decision-Sufficient V2X Experiments

Finite experiments for semantic V2X scheduling toward a MobiCom 2027 research direction. The repository contains the experiment code, frozen protocols, raw results, statistical analyses, figures, and research reports produced on 2026-09-26.

## Main finding

The experiments reject the broad claim that set utility alone outperforms a strong coverage-aware scheduler under independent delivery. They support a narrower result: under coupled message delivery such as same-channel contention, scheduling semantic evidence with the joint arrival distribution improves deadline-valid decision progress. A 140-episode CARLA 0.9.15 semantic-LiDAR closed loop reproduces the directional effect in a controlled corridor.

This repository is a feasibility package, not a complete MobiCom evaluation. The CARLA study has five paired seeds, a software link model, and a controlled scene; zero recorded collisions do not establish natural-scene safety.

## Start here

- [Full experiment report](research/full_experiment_result_20260926.md)
- [Frozen protocol](experiments/carla_v2x_full/PROTOCOL.md)
- [Reproduction instructions](experiments/carla_v2x_full/README.md)
- [CARLA validation](results/carla_v2x_full/carla_main140/analysis/validation.json)
- [Mechanism verdict](results/carla_v2x_full/mechanism_v2/analysis/verdict.json)
- [Semantic-noise robustness analysis](results/carla_v2x_full/robustness/analysis.json)

Downloaded literature PDFs and extracted full text are intentionally excluded. The reading log and research synthesis remain under `research/`.
