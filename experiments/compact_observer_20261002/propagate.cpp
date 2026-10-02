#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

// Established separable squared Euclidean distance transform. Finite lattice
// distances are exact integer-valued doubles; absent sources stay INF.
static const double INF=1e20;
static void line(const std::vector<double>& f,std::vector<double>& d,
                 std::vector<int>& v,std::vector<double>& z,int n){
  int k=-1;
  for(int q=0;q<n;++q){
    if(f[q]>=INF)continue;
    double s=-INF;
    while(k>=0){
      int p=v[k];s=((f[q]+double(q)*q)-(f[p]+double(p)*p))/(2.0*(q-p));
      if(s>z[k])break;
      --k;
    }
    ++k;v[k]=q;z[k]=(k==0?-INF:s);z[k+1]=INF;
  }
  if(k<0){std::fill(d.begin(),d.begin()+n,INF);return;}
  int j=0;
  for(int q=0;q<n;++q){
    while(z[j+1]<q)++j;
    double delta=q-v[j];d[q]=delta*delta+f[v[j]];
  }
}

extern "C" int tile_propagate(const uint8_t* possible,int64_t n,
                              double step,double distance,uint8_t* output){
  if(!possible||!output||n<1||n>2000||!std::isfinite(step)||step<=0||
     !std::isfinite(distance)||distance<0||distance>1e6)return 1;
  int m=int(n)+1;
  std::vector<double> first(int64_t(m)*m,INF),second(first.size(),INF);
  bool any=false;
  for(int i=0;i<n;++i)for(int j=0;j<n;++j){
    if(possible[int64_t(i)*n+j]>1)return 2;
    if(possible[int64_t(i)*n+j]){
      any=true;
      for(int di=0;di<2;++di)for(int dj=0;dj<2;++dj)
        first[int64_t(i+di)*m+j+dj]=0;
    }
  }
  if(any){
    std::vector<double> f(m),d(m),z(m+1);std::vector<int> v(m);
    for(int i=0;i<m;++i){
      std::copy(first.begin()+int64_t(i)*m,first.begin()+int64_t(i+1)*m,f.begin());
      line(f,d,v,z,m);
      std::copy(d.begin(),d.end(),second.begin()+int64_t(i)*m);
    }
    for(int j=0;j<m;++j){
      for(int i=0;i<m;++i)f[i]=second[int64_t(i)*m+j];
      line(f,d,v,z,m);
      for(int i=0;i<m;++i)first[int64_t(i)*m+j]=d[i];
    }
  }
  double radius=distance+1e-9,threshold=radius*radius;
  for(int i=0;i<n;++i)for(int j=0;j<n;++j){
    double best=INF;
    for(int di=0;di<2;++di)for(int dj=0;dj<2;++dj)
      best=std::min(best,first[int64_t(i+di)*m+j+dj]);
    double boundary=step*std::min(std::min(i,j),std::min(int(n)-1-i,int(n)-1-j));
    output[int64_t(i)*n+j]=uint8_t((any&&best*step*step<=threshold)||boundary<=radius);
  }
  return 0;
}
