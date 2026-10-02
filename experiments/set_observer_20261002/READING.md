# Primary-paper comparison and reading scope

1. **Narri et al., Set-Membership Estimation in Shared Situational Awareness
   for Automated Vehicles in Occluded Scenarios (2021)**.
   [Author paper](https://arxiv.org/html/2103.01791v1).
   Read abstract/introduction and §§III-B–III-C, including equations (6)–(8).
   A bounded linear pedestrian model predicts a zonotope then intersects
   measurement-consistent strips; vehicles/infrastructure share bounded
   estimates through two-level fusion. Thus shared bounded estimation and
   observation-driven uncertainty reduction are prior work. This repository's
   anonymous possible-center tile observer is a conceptual established-method
   baseline; it does not reproduce their tracked-pedestrian zonotope model,
   control law or reported simulation results.

2. **Koschi and Althoff, SPOT: A Tool for Set-Based Prediction of Traffic
   Participants (2017)**.
   [Author PDF](https://archive.air.in.tum.de/Main/Publications/Koschi2017a.pdf).
   Read abstract and §§I–II. SPOT overapproximates traffic-participant occupancy
   under bounded initial states/behaviors and uses explicit traffic-rule
   assumptions. It motivates stating all assumptions and distinguishing a
   sound overapproximation from a tight prediction. Our isotropic position
   abstraction omits its road/traffic models; it is not a SPOT reproduction
   or evidence of superiority over it.

3. **Zhang and Fisac, Safe Occlusion-aware Autonomous Driving via
   Game-Theoretic Active Perception (RSS 2021)**.
   [Conference PDF](https://www.roboticsproceedings.org/rss17/p066.pdf).
   Read §§III–IV: unknown hidden
   states, forward reachable sets, field of view and updates from subsequent
   observations. Occlusion reachability/information history are prior work;
   assumptions about adversaries and controller information are essential.
   Our static region and anonymous multi-center superset do not implement its
   reach-avoid game or complete closed-loop controller.

Only the TUM institutional abstract/bibliography was read for the 2021 TIV
occlusion-aware set-prediction follow-up; it is not claimed as a full-paper
reading. Neel/Saripalli SSRR 2020 was located by title/metadata without full
text; no technical conclusion is attributed to that paper here. No secondary
paper aggregator is used as technical evidence. This shortlist does not
establish comprehensive novelty for MobiCom 2027.
