#include <algorithm>
#include <cmath>
#include <cstdint>
extern "C" int ellipsoid_clear(const double* c,int64_t nc,const double* r,int64_t nr,double plane,double core,double outer,double error,uint8_t* out){
 if(nc<1||nc>2000||nr<1||nr>1000000||core<=0||outer<core||error<0||!std::isfinite(plane+core+outer+error))return 1;
 double bound=1+error/core+1e-8/core;
 for(int64_t j=0;j<nc;++j){
  const double* v=c+4*j;out[j]=1;
  for(int64_t i=0;i<nr;++i){
   const double* q=r+7*i;double cx=v[0]+v[2]*q[6],cy=v[1]+v[3]*q[6];
   double ex=cx-q[0],ey=cy-q[1],ez=plane-q[2],dx=q[3]-q[0],dy=q[4]-q[1],dz=q[5]-q[2];
   double x=(ex*v[2]+ey*v[3])/outer,y=(-ex*v[3]+ey*v[2])/core,z=ez/core;
   double a=(dx*v[2]+dy*v[3])/outer,b=(-dx*v[3]+dy*v[2])/core,d=dz/core;
   double den=a*a+b*b+d*d,t=den>0?(x*a+y*b+z*d)/den:0;t=std::min(1.,std::max(0.,t));
   x-=t*a;y-=t*b;z-=t*d;
   if(x*x+y*y+z*z<=bound*bound){out[j]=0;break;}
  }
 }
 return 0;
}
