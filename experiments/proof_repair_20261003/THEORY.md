# A validity interval that accounts for incomplete evidence and computation

## The quantity being computed

Fix an observation timestamp, a query/action, a motion contract and a scene family.
Let A(Y) be the states accepted by a fixed raw-observation score. For a received
message m, let Y(m) contain every raw observation consistent with its endpoint
balls and exact exceptions. Define

    X(m) = union_{Y in Y(m)} A(Y), together with the declared unknown region
    H(m) = min(500ms, inf_{x in X(m)} first_possible_contact(x, query)).

The implemented contact model is a body disc with the inherited speed and
acceleration bounds. This definition concerns that abstract model. The known
class/extent, road plane, fixed sensor transform, score and pose prior are inherited
assumptions, not inferred guarantees about an arbitrary traffic scene.

Because the current raw observation is consistent with its legal message,
A(Y_current) is contained in X(m). Missing coordinates are therefore uncertainty,
not zero-valued measurements or evidence of free space. This does not cover a
missing object, a wrongly specified shape, surface measurement error, pose error
or unmodeled motion. These require separate contracts.

## Sound repair and adaptive stopping

At every search step keep a complete partition of the pose prior. Reject a cell
only if an independently valid lower bound on the raw score exceeds the frozen
threshold for every realization of m. Splitting replaces a cell by children whose
union equals it. Old rejected cells must first be revalidated against the current
message; an old unresolved cell cannot be treated as excluded.

Let P_k be the union of retained cells plus the unknown region after k visits.
Then X(m) is contained in P_k, and exact real-arithmetic refinement gives

    L_k <= H(m),       L_{k+1} >= L_k.

An explicitly accepted pose under a legal realization of m supplies an upper
bound U_k on the capped H(m). The unknown-region boundary also supplies a model
upper bound; the 500ms cap alone supplies a trivial upper bound. Therefore

    L_k <= H(m) <= U_k,       H(m)-L_k <= U_k-L_k.

A midpoint that fails the score is not an upper witness. Failure to find any
accepted pose is not a proof that none exists. Nominal witnesses are checked with
old endpoint centers for inlier balls and exact current exceptions: one legal
realization, not necessarily the actual untransmitted raw observation.

For any stopping time K selected using the observed evidence and execution
history, the same pointwise containment gives L_K <= H(m). Thus the stopping rule
does not require selecting a fresh confidence level at every iteration. This is
a standard deterministic containment argument, not a new calibration theorem.
The numerical implementation uses floating-point guards and independent checks;
it is not a formally outward-rounded implementation of the real-arithmetic proof.

## Credibility is a coverage premise, not a consequence of long expiry

If one fixed simultaneous state set satisfies
P[x_true in A(Y)] >= 1-alpha and the action/motion contract holds, the robust
certificate inherits that event for actions whose soundness is uniform over the
admitted family. Choosing a legal compression or stopping time pointwise does not
break this containment. It also cannot establish the premise. Single-frame
coverage does not imply trajectory or mission coverage; test-dependent score
changes do not inherit an old calibration guarantee.

Here the terrain score was repaired using already observed data. Historical true
vehicle exclusions remain 3/100; synthetic coordinate changes reuse six base
observations. Neither these counts nor the independent geometry audit establishes
a deployment failure probability. No physical vehicle action is authorized by
the reported modeled positive remainder.

## Conservatism has distinct causes

With the same state/motion model and nested sets, raw evidence supports
H_raw >= H(m) >= L_k. Consequently

    H_raw - L_k = [H_raw-H(m)] + [H(m)-L_k].

The first term is loss from withheld information; the second is unresolved
computation. The earlier same-partition diagnostic measures only a restricted
part of the first term. This repair study attacks the second term but does not
identify its exact size. A declared tolerance epsilon is justified only where
U_k-L_k <= epsilon. Larger L alone cannot establish near-optimality.

In addition, the body-disc and worst-case motion model can be conservative
relative to physical motion. That model loss is outside the equality above.
It cannot be repaired merely by finding tighter pose cells.

If two admissible worlds produce the same evidence and one has immediate contact,
H(m)=0. A universally positive reliable expiry is then impossible. A useful
system must either obtain new discriminating evidence, justify a narrower scene
law/contract, change the action, or abstain. Quietly removing the adverse world
would replace conservatism with an unsupported assumption.

## Time spent proving validity consumes validity

At return, let a include source construction, encoding, transport, verification,
any initialization backlog, clock uncertainty and an action reserve. The usable
remainder is max(0,L_k-a), with action allowed only strictly before the boundary
under all stated premises. Increasing L_k can reduce this remainder if additional
computation costs more than the gain.

The tested causal heuristic stops when L_k-a >= 5ms, or when U_k <= a, with a hard
4096-visit limit. It rechecks the measured online decision cost after the native result is read.
Tree export and cleanup occur afterward in the research wrapper; its complete
API return latency is not the measured online decision latency. The 5ms
margin is not a WCET bound or proof of optimal stopping. Upper-bound expiration
only rules out a positive result under this fixed message, query, contract and
current charged time; new evidence or a different action can change the problem.

The fixed-budget experiment shows why cost is material: 4096 visits improve
geometric L in 21/36 tasks but leave zero modeled positive remainders. The adaptive
heuristic avoids some wasted work yet has median receiver cost 252.588ms versus
98.958ms for its same-trial direct baseline. It does not solve scheduling globally.

## Relation to established work

Safety-certificate reuse predates this project; see Bialkowski et al.,
[IJRR, DOI 10.1177/0278364915625345](https://journals.sagepub.com/doi/10.1177/0278364915625345)
and the [author manuscript](https://ottelab.com/html_stuff/pdf_files/Bialkowski.Otte.ea.IJRR16.pdf).
Reusing a proof or applying branch-and-bound is not itself a novelty claim.

Lindemann et al., [RA-L 2023](https://www.georgejpappas.org/wp-content/uploads/2023/08/Safe_Planning_in_Dynamic_Environments_Using_Conformal_Prediction.pdf),
derive safety from calibrated trajectory regions under explicit data and
environment assumptions. Their Assumptions 1–2 require an environment law not
changed by ego actions and independent trajectory data from that law. Our static
pose replay supplies neither such a trajectory model nor new risk calibration.

The remaining research hypothesis is that selecting additional communicated
evidence and proof work jointly can reduce the *certified* uncertainty gap while
leaving usable time. This study implements current-message proof repair and a
cost-aware stopping heuristic, not the full joint-selection problem or a proven
MobiCom contribution.
