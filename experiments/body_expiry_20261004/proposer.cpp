// Floating proposals only. Python integer certificates decide acceptance.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
#include <random>
struct P {long double x,y;};
P operator+(P a,P b){return {a.x+b.x,a.y+b.y};} P operator-(P a,P b){return {a.x-b.x,a.y-b.y};} P operator*(P a,long double z){return {a.x*z,a.y*z};}
long double dot(P a,P b){return a.x*b.x+a.y*b.y;} long double cross(P a,P b){return a.x*b.y-a.y*b.x;} long double norm2(P a){return dot(a,a);}
struct Circle {P c;long double r2;int n,ids[3];};
Circle paircircle(P a,P b,int i,int j){P c=(a+b)*.5L;return {c,norm2(a-c),2,{i,j,-1}};}
Circle triangle(P a,P b,P c,int i,int j,int k){P u=b-a,v=c-a;long double det=2*cross(u,v);if(det==0){Circle x=paircircle(a,b,i,j),y=paircircle(a,c,i,k),z=paircircle(b,c,j,k);return x.r2>=y.r2&&x.r2>=z.r2?x:y.r2>=z.r2?y:z;}P off={(norm2(u)*v.y-norm2(v)*u.y)/det,(u.x*norm2(v)-v.x*norm2(u))/det};return {a+off,norm2(off),3,{i,j,k}};}
Circle minimal(const std::vector<P>& c,const std::vector<int>& b){
 if(b.empty())return {{0,0},-1,0,{-1,-1,-1}};
 if(b.size()==1)return {c[b[0]],0,1,{b[0],-1,-1}};
 if(b.size()==2)return paircircle(c[b[0]],c[b[1]],b[0],b[1]);
 Circle best=triangle(c[b[0]],c[b[1]],c[b[2]],b[0],b[1],b[2]);
 for(int i=0;i<3;i++)for(int j=i+1;j<3;j++){auto t=paircircle(c[b[i]],c[b[j]],b[i],b[j]);bool ok=true;for(auto k:b)if(norm2(c[k]-t.c)>t.r2+1e-8L)ok=false;if(ok&&t.r2<best.r2)best=t;}return best;
}
Circle welzl(const std::vector<P>& c,const std::vector<int>& order,int n,std::vector<int> b){
 if(n==0||b.size()==3)return minimal(c,b);int k=order[n-1];Circle m=welzl(c,order,n-1,b);if(m.r2>=0&&norm2(c[k]-m.c)<=m.r2+std::max(1e-8L,m.r2*1e-18L))return m;b.push_back(k);return welzl(c,order,n-1,b);
}
extern "C" int hull(const int64_t* in,int n,int64_t* out){
 std::vector<std::pair<int64_t,int64_t>> v;for(int i=0;i<n;i++)v.push_back({in[2*i],in[2*i+1]});std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());if(v.size()<2){for(int i=0;i<(int)v.size();i++){out[2*i]=v[i].first;out[2*i+1]=v[i].second;}return v.size();}
 auto turn=[](auto a,auto b,auto c){return (__int128)(b.first-a.first)*(c.second-a.second)-(__int128)(b.second-a.second)*(c.first-a.first);};std::vector<std::pair<int64_t,int64_t>> h;
 for(auto p:v){while(h.size()>=2&&turn(h[h.size()-2],h.back(),p)<=0)h.pop_back();h.push_back(p);}size_t lower=h.size();for(int i=(int)v.size()-2;i>=0;i--){auto p=v[i];while(h.size()>lower&&turn(h[h.size()-2],h.back(),p)<=0)h.pop_back();h.push_back(p);}h.pop_back();for(int i=0;i<(int)h.size();i++){out[2*i]=h[i].first;out[2*i+1]=h[i].second;}return h.size();
}
extern "C" int propose(const int64_t* in,int n,int64_t radius,int64_t qx,int64_t qy,int64_t* point,int64_t* anchor,int* active,int64_t* weights,int* mec_ids){
 if(n<=0)return 4;std::vector<P> c;for(int i=0;i<n;i++)c.push_back({(long double)in[2*i],(long double)in[2*i+1]});long double R=radius,R2=R*R,tol=std::max(1e-8L,R2*1e-15L);P q={(long double)qx,(long double)qy};std::vector<int> order;for(int i=0;i<n;i++)order.push_back(i);std::mt19937 rng(20261004);std::shuffle(order.begin(),order.end(),rng);Circle m=welzl(c,order,n,{});
 for(int k=0;k<3;k++)mec_ids[k]=k<m.n?m.ids[k]:-1;
 for(int k=0;k<2;k++)anchor[k]=llround((k?m.c.y:m.c.x)*1000000.L);
 if(m.r2>R2+tol)return 2;
 auto feasible=[&](P p){for(auto a:c)if(norm2(p-a)>R2+tol)return false;return true;};P best;long double bestd=INFINITY,bw0=0,bw1=0;int bi=-1,bj=-1;
 auto consider=[&](P p,int i,int j,long double w0,long double w1){if(!feasible(p))return;long double d=norm2(p-q);if(d<bestd){best=p;bestd=d;bi=i;bj=j;bw0=std::max(0.L,w0);bw1=std::max(0.L,w1);}};
 for(int i=0;i<n;i++){P v=q-c[i];long double length=sqrtl(norm2(v));if(length>0)consider(c[i]+v*(R/length),i,-1,1,0);}
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){P v=c[j]-c[i];long double d2=norm2(v);if(d2==0||d2>4*R2+tol)continue;long double h2=std::max(0.L,R2-d2*.25L);P mid=(c[i]+c[j])*.5L,perp={-v.y/sqrtl(d2),v.x/sqrtl(d2)};for(int sign:{-1,1}){P p=mid+perp*(sign*sqrtl(h2));P t0=p-c[i],t1=p-c[j],dir=q-p;long double det=cross(t0,t1);if(det==0)continue;long double w0=cross(dir,t1)/det,w1=cross(t0,dir)/det;if(w0>=-1e-12L&&w1>=-1e-12L)consider(p,i,j,w0,w1);}}
 if(!std::isfinite(bestd))return 4;
 point[0]=llround(best.x*1000000.L);point[1]=llround(best.y*1000000.L);active[0]=bi;active[1]=bj;long double w=std::max(bw0,bw1);weights[0]=w>0?llround(bw0/w*1000000000000.L):0;weights[1]=w>0?llround(bw1/w*1000000000000.L):0;return 0;
}
