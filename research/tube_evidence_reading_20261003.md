# Certificate reuse is prior art; current-evidence precision is the remaining question

Read scope: publisher metadata/abstract and targeted author-PDF passages on methods,
assumptions, sharing and evaluation; not a claim of exhaustive whole-paper review.
Accessed 2026-10-03. These papers supplement the prior literature notes in this repo.

1. Bialkowski, Otte, Karaman, Frazzoli, *Efficient collision checking in sampling-based
   motion planning via safety certificates*, IJRR 35(7), 767–796, 2016.
   [Publisher / correct DOI](https://journals.sagepub.com/doi/10.1177/0278364915625345),
   [author manuscript](https://ottelab.com/html_stuff/pdf_files/Bialkowski.Otte.ea.IJRR16.pdf).
   Cached distance-to-obstacle bounds certify nearby configurations, with asymptotic
   collision-checking analysis under specified sampling and obstacle assumptions.
   Reusing a geometric certificate to avoid repeated checking is established prior
   art. Its asymptotic theorem does not by itself cover uncertain current LiDAR
   evidence or provide our source-time action deadline. The author PDF has stale
   template DOI/year fields; bibliographic metadata here follows the publisher.

2. Otte, Bialkowski, Frazzoli, *Any-Com Collision Checking: Sharing Certificates in
   Decentralized Multi-Robot Teams*, ICRA 2014, 563–570.
   [Author-hosted paper](https://ottelab.com/html_stuff/pdf_files/Otte.Bialkowski.ea.ICRA14.pdf).
   Shared certificates reduce duplicate collision checking. The paper evaluates
   communication quality and includes wireless-laptop experiments as well as
   simulation. Certificate sharing under imperfect communication is therefore not
   a new contribution of this project. Our candidate distinction is revalidating
   evidence from a fresh partial observation, explicitly preserving all represented
   returns and charging the action time lost to representation and computation.
   That distinction still needs evidence of usefulness and comparison with strong
   systems baselines; terminology alone is insufficient.

Current research inference: focus on an auditable tradeoff between current-evidence
precision, computation and useful validity time. Endpoint balls are a conservative
geometric representation, not a newly invented uncertainty principle. The present
experiment tests one mechanism for that tradeoff. It cannot yet establish a
MobiCom-level contribution, complete risk calibration or near-optimal horizons.

## Additional current and foundational comparisons

3. Bhatt et al., *UNCAP: Uncertainty-Guided Neurosymbolic Planning Using Natural
   Language Communication for Cooperative Autonomous Vehicles*, AAMAS2026,
   [author manuscript v2, 12 January2026](https://arxiv.org/html/2510.12992v2).
   Read sections3.1–3.5, including partner-selection rules, per-object uncertainty,
   fusion and VLM planning. The method already combines selective semantic messages
   and uncertainty. Our inference: class-label coverage and a plan confidence score
   do not automatically certify an entire occupied-region trajectory or a deadline
   for withheld current LiDAR returns. Comparing these different objects requires
   an explicit mapping of failure events. This is a scope distinction, not a claim
   that our prototype outperforms UNCAP; its implementation was not reproduced.

4. Lindemann, Cleaveland, Shim, Pappas, *Safe Planning in Dynamic Environments Using
   Conformal Prediction*, IEEE RA-L8(8),2023, DOI10.1109/LRA.2023.3292071.
   [Author-hosted paper](https://www.georgejpappas.org/wp-content/uploads/2023/08/Safe_Planning_in_Dynamic_Environments_Using_Conformal_Prediction.pdf).
   Read assumptions1–2, Theorems1–3, Remarks3–4 and the CARLA case-study scope.
   It propagates trajectory prediction regions into MPC constraints with explicit
   multi-step risk accounting. Its stated assumptions include unchanged trajectory
   distribution under ego control and appropriate offline trajectory samples;
   closed-loop safety also assumes feasibility at each step. Conformal regions plus
   robust planning are therefore established methods. Our interpretation: this
   project's retrospective pose scores cannot inherit those trajectory guarantees,
   and marginal single-observation coverage cannot be called mission-wide safety.

Search also returned2026 work on uncertainty-guided collaboration and adaptive
safety margins. Abstract-only or inaccessible records are not used to claim a
methodological gap. No assertion of exhaustive novelty clearance is made.

5. Shin et al., *RECAP: 3D Traffic Reconstruction*, MobiCom2024.
   [Author-hosted paper](https://fawadahm.github.io/assets/pdf/Recap_Mobicom_2024.pdf).
   Read introduction and architecture/registration/temporal-expansion passages.
   RECAP streams compressed point clouds and addresses multi-view alignment and
   traffic reconstruction. Our fixed identical-transform RSU fixture avoids an
   important systems difficulty addressed there. We should not portray raw
   uncompressed point-cloud transfer as the only alternative to task evidence.
   Its reconstruction objective differs from the current action-deadline query;
   no quantitative system comparison is made here.

6. Feng, Liu, Zhu, *Real-Time Spatio-Temporal LiDAR Point Cloud Compression*,2020.
   [Author-hosted manuscript](https://horizon-lab.org/pubs/iros20.pdf),
   [arXiv record](https://arxiv.org/abs/2008.06972).
   Read the overview and spatial/temporal encoding passages. Reusing a reference
   representation across LiDAR frames to reduce bytes and redundant work is also
   prior art. Our endpoint-ball codec is a test vehicle for conservative evidence
   propagation, not a claim of a generally superior or novel temporal compressor.
   Future performance comparisons need efficient bounded-distortion and temporal
   codecs paired with the same evidence verifier and error contract.
