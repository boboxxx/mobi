#include <cmath>
#include <cstdint>
#include <algorithm>

extern "C" int ray_mask(int64_t nw, const double* w, int64_t n,
                       double domain,double step,unsigned char* out) {
 if(nw<0||nw>500000||n<1||n>2000||!std::isfinite(domain)||
    !std::isfinite(step)||domain<=0||step<=0||std::abs(n*step-2*domain)>1e-7)return -1;
 std::fill(out,out+n*n,0);
 double axis=-domain+.5*step;
 for(int64_t k=0;k<nw;++k) {
  double x=w[3*k],y=w[3*k+1],r=w[3*k+2];
  if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(r))return -1;
  if(r<=0)continue;
  auto clamp=[n](double v){return std::max(-1.,std::min((double)n,v));};
  int64_t lx=std::max((int64_t)0,(int64_t)clamp(std::floor((x-r-axis)/step)-1));
  int64_t hx=std::min(n-1,(int64_t)clamp(std::ceil((x+r-axis)/step)+1));
  int64_t ly=std::max((int64_t)0,(int64_t)clamp(std::floor((y-r-axis)/step)-1));
  int64_t hy=std::min(n-1,(int64_t)clamp(std::ceil((y+r-axis)/step)+1));
  for(auto i=lx;i<=hx;++i)for(auto j=ly;j<=hy;++j) {
   double dx=(-domain+(i+.5)*step)-x,dy=(-domain+(j+.5)*step)-y;
   if(std::sqrt(dx*dx+dy*dy)<r)out[i*n+j]=1;
  }
 }
 return 0;
}
