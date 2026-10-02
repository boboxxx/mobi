# Primary-source reading and candidate boundaries,2026-10-02

These notes describe reading scope, not reproduced paper experiments. No
peer-reviewed acceptance is inferred for an arXiv preprint.

- [Chung et al., APRO, arXiv2606.15046v1](https://arxiv.org/html/2606.15046v1),
  June13,2026. Read abstract, introduction/related work, preliminaries,
  assumptions, Theorems4–5/LP condition and both control schemes through V.
  Joint affine states and AH-polyhedron unions allow exact set checks relative
  to the paper's model. Passive safety treats stopping differently from
  universal collision avoidance. Adding state correlation or backup control
  alone is insufficient novelty here; its polyhedral/affine assumptions do not
  directly reproduce our Euclidean acceleration/ray-error contract.

- [Kim et al., OcclusionCBF, arXiv2609.06342v1](https://arxiv.org/html/2609.06342v1).
  Read abstract/introduction, hidden occupancy coverage and temporal consistency,
  backup/verified-terminal conditions, recursive feasibility and IV-E.
  A continuous obstacle speed cap differs from our speed-at-observation model.
  Discontinuous predictions require recertification. The ideal continuous
  constraint family and implemented temporal sampling are explicitly distinct.
  We must verify an invariant terminal set before borrowing its safety claim;
  a finite brake rollout alone does not establish that condition.

- [Janson, Hu, Pavone, RSS2018](https://www.roboticsproceedings.org/rss14/p61.pdf),
  *Safe Motion Planning in Unknown Environments: Optimality Benchmarks and
  Tractable Policies*. Read abstract/introduction and the beginning of notation;
  later proofs/algorithms/experiments not fully read this turn. Available
  information matters to the benchmark. We do not claim that their optimality
  notion is equivalent to our received-ray continuous-occupancy lifetime.

Candidate question: can a V2X system certify a received-evidence lifetime AND
a useful bound on its conservatism, then exchange extra real observations when
the gap is unresolved, accounting for delivery/verification age and loss?
The implemented finite lower/trajectory-upper diagnostics expose an actual
sender/receiver information gap. They do not establish firstness or an optimal
online exchange algorithm. Strong fixed-region and exact transport baselines
must remain; changing scenes, paid adaptive evidence selection, realized moving
actions, physical contracts and actual links remain required for MobiCom.
