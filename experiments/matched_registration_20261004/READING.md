# Primary-paper reading and boundaries of the next question

**Hu et al., Zero-Shot Semantic Communication with Multimodal Foundation
Models**, arXiv2502.18200v2,29May2025; v1 used a task-agnostic title.
[Author full text](https://arxiv.org/html/2502.18200), sectionsI–V including
system assumptions, two-stage training, zero-shot classification/retrieval and
implementation costs. SemCLIP transmits general image tokens and adapts the
receiver to task prompts. Consequently, unknown downstream tasks and one
representation supporting later queries are existing ideas. Its evaluated
prediction/retrieval metrics do not establish our current-state coverage or
source-aged physical lifetime. That is a difference in objective, not evidence
that our system beats it or that query reuse is novel.

**Barbier et al., Lipschitz Pruning: Hierarchical Simplification of
Primitive-Based SDFs**, Computer Graphics Forum44(2), Eurographics2025.
[Author full PDF](https://wbrbr.org/publications/LipschitzPruning/documents/LipschitzPruning_submitted_to_EG25.pdf), introduction/related work,3.2–3.5,
experimental discussion,6 andAppendixA. The method prunes implicit distance
expressions using regional Lipschitz bounds and preserves their values; it
also discusses conservative distance bounds and far-field replacement.
Distance-field reuse, conservative Lipschitz envelopes and regional pruning
are prior art, not our inventions. Our state-set field would be a nonnegative
distance to a calibrated possible-center set, not a reconstructed signed mesh
distance. Before any novelty claim we must compare against a generic certified
sampled distance field and exact hull reuse under matched paid costs.

**Shao, Li, Zhang, TOCOM-V2I**, arXiv2407.20748v1.
[Author full text](https://arxiv.org/html/2407.20748), model/problem formulation
and feature-selection/entropy/fusion methods. It targets V2I detection utility
under rate cost; multi-round communication latency is already identified as
a constraint. We cannot call task-relevant compression or avoiding request
round trips a new contribution. We have no trained-feature benchmark result
against this system; its detection setup differs from our declared known actor.

**Wei et al., Task-Agnostic Semantic Communications Relying on Information
Bottleneck and Federated Meta-Learning**, arXiv2504.21723v2. Read introduction,
system/DMIB definitions andIII-B inner/outer adaptation from the
[author full text](https://arxiv.org/html/2504.21723v2); this is a targeted
method reading, not a claimed full-paper replication. Multi-task sufficiency
and adaptation are existing themes. Reusing our fixed whole-state event for
new queries does not create a new task-agnostic communication principle.

The immediate matched-registration experiment tests a fairness gap in our
previous cost comparison. These papers motivate possible next comparisons;
they are not experimental evidence for the current implementation.
