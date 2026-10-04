"""Exact fixed-law useful-progress lower bound; standard binomial inference."""
import math
from fractions import Fraction as F

def tail(k,n,p):
 p=F(p);assert 0<=k<=n and 0<=p<=1
 return sum(F(math.comb(n,j))*p**j*(1-p)**(n-j) for j in range(k,n+1))
def certificate(useful,minimum=F(1,4),delta=F(1,120)):
 useful=list(useful);assert useful and all(type(v) is bool for v in useful)
 n=len(useful);k=sum(useful);pv=tail(k,n,minimum);lo=F(0);hi=F(1)
 if k:
  for _ in range(64):
   mid=(lo+hi)/2
   if tail(k,n,mid)<=delta:lo=mid
   else:hi=mid
 accepted=bool(k and pv<=delta)
 if accepted:lo=max(lo,minimum)
 return dict(planned=n,useful=k,minimum=[minimum.numerator,minimum.denominator],lower=[lo.numerator,lo.denominator],p_value=[pv.numerator,pv.denominator],accepted=accepted)
