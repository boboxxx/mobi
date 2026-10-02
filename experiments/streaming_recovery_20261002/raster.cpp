#include <cmath>
#include <cstdint>
#include <vector>
#include "../usable_lease_20261002/cover.cpp"

// Enumerate actual lattice centers in each individual strict witness ball.
// maps gives required-cell identities, -1 for unused tiles, across all classes.
// mode0 verifies coverage; mode1 constructs CSR for established greedy.
extern "C" int64_t raster_cover(int64_t rays, int64_t cells, int64_t nw,
 const double* w, const int64_t* ids, const int64_t* classes,
 int64_t nc, const int64_t* dims, const int64_t* starts,
 const double* axes, const double* steps, int64_t nm, const int64_t* maps,
 int mode, int64_t* output) {
 if(rays<0||rays>500000||cells<0||cells>2000000||nw<0||nw>1000000||
    nc<1||nc>16||nm<0||nm>4000000||(mode!=0&&mode!=1)) return -1;
 for(int64_t c=0;c<nc;++c) {
   if(dims[c]<1||dims[c]>2000||starts[c]<0||
      starts[c]+dims[c]*dims[c]>nm||!std::isfinite(axes[c])||
      !std::isfinite(steps[c])||steps[c]<=0) return -1;
 }
 for(int64_t i=0;i<nm;++i) if(maps[i]<-1||maps[i]>=cells) return -1;
 std::vector<unsigned char> covered(cells,0);
 std::vector<std::vector<int64_t>> rows(mode==1?rays:0);
 int64_t edges=0;
 for(int64_t k=0;k<nw;++k) {
   auto c=classes[k];auto id=ids[k];auto x=w[3*k],y=w[3*k+1],r=w[3*k+2];
   if(c<0||c>=nc||id<0||id>=rays||!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(r)) return -1;
   if(r<=0) continue;
   auto n=dims[c];double s=steps[c],domain=axes[c],a=-domain+.5*s;
   // Clamp in floating point before integer conversion, including far witnesses.
   int64_t loX=(int64_t)std::max(0.,std::min((double)n,std::floor((x-r-a)/s)-1));
   int64_t hiX=(int64_t)std::max(-1.,std::min((double)n-1,std::ceil((x+r-a)/s)+1));
   int64_t loY=(int64_t)std::max(0.,std::min((double)n,std::floor((y-r-a)/s)-1));
   int64_t hiY=(int64_t)std::max(-1.,std::min((double)n-1,std::ceil((y+r-a)/s)+1));
   for(auto i=loX;i<=hiX;++i) for(auto j=loY;j<=hiY;++j) {
     auto cell=maps[starts[c]+i*n+j];if(cell<0)continue;
     // Same center expression as geometry.grid, avoiding reassociation.
     double dx=(-domain+(i+.5)*s)-x;
     double dy=(-domain+(j+.5)*s)-y;
     if(std::sqrt(dx*dx+dy*dy)<r) {
       covered[cell]=1;
       if(mode==1) {if(++edges>20000000)return -1;rows[id].push_back(cell);}
     }
   }
 }
 for(auto hit:covered)if(!hit)return -2;
 if(mode==0)return 0;
 std::vector<int64_t> ptr(rays+1,0),col,order(rays);
 col.reserve(edges);
 for(int64_t i=0;i<rays;++i) {
   std::sort(rows[i].begin(),rows[i].end());
   rows[i].erase(std::unique(rows[i].begin(),rows[i].end()),rows[i].end());
   col.insert(col.end(),rows[i].begin(),rows[i].end());ptr[i+1]=col.size();order[i]=i;
 }
 return cover_select(rays,cells,col.size(),ptr.data(),col.data(),order.data(),1,output);
}
