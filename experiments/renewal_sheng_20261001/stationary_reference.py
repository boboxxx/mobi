"""Small-model discounted value iteration; generic strong scheduling reference."""
from functools import lru_cache
import itertools
import numpy as np
from scheduler import advance, valid


@lru_cache(maxsize=64)
def build(ttl, required, guard, service, p, gamma=.99):
    states=list(itertools.product(*(range(1,t+2) for t in ttl)))
    ids={s:i for i,s in enumerate(states)};actions=(None,)+required
    success=np.zeros((len(states),len(actions)),dtype=int);failure=success.copy()
    probability=np.zeros_like(success,dtype=float)
    for i,state in enumerate(states):
        for j,action in enumerate(actions):
            success[i,j]=ids[advance(state,ttl,action,True,service)]
            failure[i,j]=ids[advance(state,ttl,action,False,service)]
            probability[i,j]=p if action is not None else 0.
    r=np.array([valid(s,ttl,required,guard) for s in states],dtype=float)
    immediate=probability*r[success]+(1-probability)*r[failure]
    value=np.zeros(len(states));residual=None
    for iteration in range(5000):
        q=immediate+gamma*(probability*value[success]+(1-probability)*value[failure])
        nxt=q.max(axis=1);residual=float(np.max(np.abs(nxt-value)));value=nxt
        if residual<1e-10:break
    else:raise RuntimeError('Value iteration did not converge')
    q=immediate+gamma*(probability*value[success]+(1-probability)*value[failure])
    policy={}
    for i,state in enumerate(states):
        j=max(range(len(actions)),key=lambda j:(round(float(q[i,j]),9),float(immediate[i,j]),actions[j] is None,-j))
        policy[state]=actions[j]
    return policy,dict(states=len(states),iterations=iteration+1,residual=residual,gamma=gamma,
                      value_error_bound=residual/(1-gamma))


def choose(ages,ttl,required,guard,service,p):
    return build(tuple(ttl),tuple(required),guard,service,p)[0][tuple(ages)]
