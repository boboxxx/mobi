"""Conservative pose-cell score bound for OBB intersected with z>=0.15."""
import importlib.util,sys
from pathlib import Path
from fractions import Fraction
import numpy as np
# Load original modules under their original dependency names; do not shadow bounds.
POSE=Path(__file__).resolve().parents[1]/'pose_inversion_20261003'
def make_index_class():
    from refined import RefinedIndex,refined_enclosures
    class TerrainIndex(RefinedIndex):
        def interval(self,o,d,e,world_dz):
            lo=np.zeros(len(d));hi=np.full(len(d),np.inf);valid=np.ones(len(d),bool)
            for j in range(3):
                nz=abs(d[:,j])>1e-12;valid&=nz|(abs(o[j])<=e[j]);a=np.divide(-e[j]-o[j],d[:,j],out=np.full(len(d),-np.inf),where=nz);b=np.divide(e[j]-o[j],d[:,j],out=np.full(len(d),np.inf),where=nz);lo=np.maximum(lo,np.minimum(a,b));hi=np.minimum(hi,np.maximum(a,b))
            up=world_dz>1e-12;down=world_dz< -1e-12;flat=~(up|down);valid&=~flat|(self.origin[2]>=.15);cross=np.divide(.15-self.origin[2],world_dz,out=np.zeros(len(d)),where=~flat);lo=np.maximum(lo,np.where(up,cross,-np.inf));hi=np.minimum(hi,np.where(down,cross,np.inf));return valid&(hi>=lo)&(lo<=1+1e-10),hi
        def bound(self,cell,extent,anchor,road_rotation,indexed=True,anisotropic=True):
            center,r,inner,outer=refined_enclosures(cell,extent,anchor,road_rotation);o=(self.origin-center)@r
            if np.any(inner<=0) or np.all(abs(o)<=outer):return dict(numerator=0,denominator=1,reason='unresolved_enclosure',examined=0)
            ids=self.candidates(center,outer,indexed);d=self.d[ids]@r;dz=self.d[ids,2];possible,leave=self.interval(o,d,outer,dz);definite,_=self.interval(o,d,inner,dz);n=int(possible.sum());m=int(definite.sum());k=int(np.sum(definite&(leave<1-1e-10)));h=int(np.sum(possible&(leave>=1-1e-10)));assert k<=m<=n;b=Fraction(0)
            if m>=8:b=max(Fraction(k,n),Fraction(max(0,m-h),m))
            return dict(numerator=b.numerator,denominator=b.denominator,definitely_eligible=m,possibly_eligible=n,definitely_passed=k,possibly_nonpassing=h,reason=None if m>=8 else 'insufficient_guaranteed_support',examined=len(ids))
    return TerrainIndex
