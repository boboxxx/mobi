#include <algorithm>
#include <cmath>
#include <cstdint>
extern "C" int clear_candidates(const double* candidates,int64_t count,const double* rays,int64_t nr,double plane,double radius,uint8_t* out){
 if(count<1||count>2000||nr<1||nr>1000000||!std::isfinite(plane)||!std::isfinite(radius)||radius<=0)return 1;
 for(int64_t j=0;j<count;++j){
  const double* c=candidates+4*j;out[j]=1;
  for(int64_t i=0;i<nr;++i){
   const double* r=rays+7*i;
   double x=c[0]+c[2]*r[6],y=c[1]+c[3]*r[6],z=plane;
   double dx=r[3]-r[0],dy=r[4]-r[1],dz=r[5]-r[2];
   double norm=dx*dx+dy*dy+dz*dz;
   double t=norm>0?((x-r[0])*dx+(y-r[1])*dy+(z-r[2])*dz)/norm:0;
   t=std::min(1.,std::max(0.,t));
   double ex=x-r[0]-t*dx,ey=y-r[1]-t*dy,ez=z-r[2]-t*dz;
   if(ex*ex+ey*ey+ez*ez<=radius*radius){out[j]=0;break;}
  }
 }
 return 0;
}
