# Conditional maximal expiry of intersected current supports

Let S_v be the union of all quantized-center q-discs from an available current
view. The already-frozen episode event E is that every output S_v covers the
true current center at its source snapshot. No authority is created by refusal.
For identical frame/epoch, E implies x in C=S_0 intersect S_1. View dependence
does not matter to this implication because E was calibrated simultaneously.
Selecting or computing subsets downstream preserves this implication on E;
there is no second learned score or nominal independence of the views.

With body/query radius b and displacement D(t)=5t+1.5t^2 (meters, seconds), the
guaranteed noncontact condition is dist(query,C)>b+D(t). C is a finite union of
closed convex lenses. Its exact distance is the minimum over all nonempty
component-pair lens distances. A closest feasible point proves an upper bound;
all-pair lower certificates prove a lower bound. If C is empty, E is false and
the receiver must detect a contradiction, not infer that the road is empty.

For a lens, any direction t_i and nonnegative integer weight w_i obey
 t_i.x <= t_i.c_i + q*norm(t_i).
Set u=-sum(w_i*t_i). Then every lens point satisfies
 norm(x-query) >= [sum w_i(t_i.(query-c_i)-q*norm(t_i))]/norm(u).
Upper-rounded norms in numerator subtraction and denominator, followed by
flooring, give a valid integer lower bound. A rational feasible point and
upper-rounded distance give the upper bound. Exact tangent pairs are singletons;
query-inside witnesses give zero. Decimal only proposes witnesses/weights;
independent integer checks justify the final bracket. No floating optimum is
trusted. Integer strict contact checks invert D for the last safe microsecond.

This is the maximal guaranteed horizon in the declared unrestricted center-set
and isotropic displacement model, up to the saved bracket and500ms cap: beyond
the exact contact threshold, a closest supported center plus allowed displacement
can touch the query disk. It does not prove that every model state is compatible
with the original rays, that every permitted displacement is physically
realizable, or that model ambiguity equals raw-observation ambiguity.

C is a subset of each S_v, so geometric expiry weakly improves on the best
single-view expiry when nonempty. Computational delay, queue changes and
contradictions can erase this gain. Utility must be measured after all fees.
The statistical promise still refers to the inherited current-state event and
explicit motion/body assumptions. The one inherited Motorcycle test exclusion
cannot be erased by a zero observed grant-conflict count.
