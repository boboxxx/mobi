# Primary reading and implications, 2026-10-02

Reading scope is explicit. No paper's experiments are reproduced by this
package, and an arXiv version is not assumed to have peer-reviewed acceptance.

- [Hu et al., Where2comm, NeurIPS2022 proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/file/1f5c5cd01b864d53cc5fa0a3472e152e-Paper-Conference.pdf).
  Read abstract/introduction, problem formulation, spatial confidence and
  request-map selection (Sections4.2–4.3), and stated limitations. The method
  exchanges sparse features conditioned on detection confidence and peer
  requests. It explicitly recognizes that low confidence can mean either
  emptiness or missing information. Our inference: selection by information
  need is already established; a contribution must demonstrate a different,
  measurable objective and stronger evidence than renaming confidence as
  semantics. Our candidate objective is paid, verifiable future action time.
  Detailed experiments and appendix were not fully read in this continuation.

- [Chiu and Smith, Selective Communication for Cooperative Perception in
  End-to-End Autonomous Driving, arXiv2305.17181v1](https://arxiv.org/html/2305.17181v1).
  Read abstract, related work and SectionsIII-A–B. Sparse detected-center
  exchange ranks peers by objects missing from the ego detections; chosen
  peers then send denser features for control. This is an existing two-round
  information-gain selection design. Our inference: an extra-evidence request
  is not itself new; our costs must also include discovery, selection and
  verification. Architecture/experimental sections were not fully read here.

- [Gan et al., SComCP, arXiv2507.00895v1](https://arxiv.org/html/2507.00895v1).
  Read abstract and SectionII system/problem formulation through the opening
  of SectionIII. Importance-selected BEV features pass through a noisy-channel
  semantic codec and fusion/detection; the stated perception objective uses
  AP. Our inference: learned feature selection and JSCC are established nearby
  approaches, but their reported AP cannot substitute for a per-instance
  expiration proof. Detailed architecture, training and results were not fully
  read in this continuation, so no quantitative superiority claim is made.

- [Ma et al., Real-time identification of cooperative perception necessity in
  road traffic scenarios, Transportation Research C,2026](https://www.sciencedirect.com/science/article/pii/S0968090X26000355).
  Read the publisher abstract, highlights and introduction; full methods were
  not accessible in that page view. Collision risk and perception blind spots
  are combined to identify CP need, with field-test evaluation. Our inference:
  safety-driven communication necessity is already a close prior direction;
  "send only when risky" cannot be the claimed contribution by itself.

The previous [APRO/OcclusionCBF reading](../validity_witness_20261002/READING.md)
also remains binding on novelty claims: set prediction, joint hidden states,
and verified backups are established. The finite new result isolates one
potentially useful issue: evidence for a class that does not limit current
joint expiry can preserve a future proof chain. The present fixed525/475
targets and negative paid-utility result do not yet establish a new algorithm.
An adaptive mechanism must beat strong fixed-region and same-information
positional baselines with every cost charged, and survive changing scenes.
