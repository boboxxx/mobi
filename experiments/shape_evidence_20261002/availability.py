"""Observable missing inputs produce a full prediction set, never an exclusion."""
from fractions import Fraction
FAMILY=frozenset((view,stride) for view in (0,1) for stride in (1,4,16))

def family_assessment(scores,threshold):
    if not 0<=threshold<=1:raise ValueError('Threshold')
    if set(scores)!=FAMILY:
        return dict(available=False,nonconformity=Fraction(0),excluded_cases=[])
    for s in scores.values():
        if s['denominator']<=0 or not 0<=s['numerator']<=s['denominator']:raise ValueError('Score')
    values={k:Fraction(s['numerator'],s['denominator']) for k,s in scores.items()}
    return dict(available=True,nonconformity=max(values.values()),excluded_cases=sorted(k for k,s in scores.items() if s['reason'] is None and values[k]>threshold))
