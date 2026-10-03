#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <queue>
#include <stdexcept>
#include <vector>
#include <chrono>
using V=std::array<double,3>;using M=std::array<double,9>;
V add(V a,V b){for(int i=0;i<3;i++)a[i]+=b[i];return a;}
V sub(V a,V b){for(int i=0;i<3;i++)a[i]-=b[i];return a;}
double dot(V a,V b){double x=0;for(int i=0;i<3;i++)x+=a[i]*b[i];return x;}
double norm(V a){return std::sqrt(dot(a,a));}
V mv(M a,V x){V y{};for(int i=0;i<3;i++)for(int j=0;j<3;j++)y[i]+=a[3*i+j]*x[j];return y;}
M trans(M a){M b{};for(int i=0;i<3;i++)for(int j=0;j<3;j++)b[3*i+j]=a[3*j+i];return b;}
M mm(M a,M b){M c{};for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++)c[3*i+j]+=a[3*i+k]*b[3*k+j];return c;}
M eye(){return {1,0,0,0,1,0,0,0,1};}
M rot(double p,double y,double r){double cp=cos(p),sp=sin(p),cy=cos(y),sy=sin(y),cr=cos(r),sr=sin(r);return {cp*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr,cp*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr,sp,-cp*sr,cp*cr};}
// Bounded research model only: v=5m/s, a=3m/s^2, task radius=.75m, cap=.5s.
// Reduced exact reach denominator 2e6 keeps every product within128 bits.
bool safe(int64_t x,int64_t y,int64_t r,int t){using U=__uint128_t;U rr=U(2000000)*U(r+750000)+U(10000000)*U(t)+U(3)*U(t)*U(t);return (U(x)*x+U(y)*y)*U(4000000000000ULL)>rr*rr;}
int age(int64_t x,int64_t y,int64_t r){if(!safe(x,y,r,0))return 0;if(safe(x,y,r,500000))return 500000;double c=std::hypot(double(x),double(y))-double(r+750000);double t=2*c/(5000000.+std::sqrt(25000000000000.+6000000.*c));int guess=std::max(0,std::min(499999,int(std::floor(t*1000000.))));while(guess>0&&!safe(x,y,r,guess))--guess;while(guess<500000&&safe(x,y,r,guess+1))++guess;return guess;}
struct Ray {V d,u;int stride;};
struct KNode {int ray,left=-1,right=-1,axis;};
struct Rays {V origin;std::vector<Ray> rays;std::vector<KNode> nodes;int root=-1;
 int build(std::vector<int>& ids,int lo,int hi,int depth){if(lo==hi)return -1;int mid=(lo+hi)/2,axis=depth%3;std::nth_element(ids.begin()+lo,ids.begin()+mid,ids.begin()+hi,[&](int a,int b){return rays[a].u[axis]<rays[b].u[axis];});int n=nodes.size();nodes.push_back({ids[mid],-1,-1,axis});int l=build(ids,lo,mid,depth+1),r=build(ids,mid+1,hi,depth+1);nodes[n].left=l;nodes[n].right=r;return n;}
 Rays(const double* points,const int* stride,int count,V o):origin(o){rays.reserve(count);std::vector<int> ids;for(int i=0;i<count;i++){V d={points[3*i]-o[0],points[3*i+1]-o[1],points[3*i+2]-o[2]};double len=norm(d);V u{};if(len>1e-12){for(int j=0;j<3;j++)u[j]=d[j]/len;ids.push_back(i);}rays.push_back({d,u,stride[i]});}nodes.reserve(count);root=build(ids,0,ids.size(),0);}
 template<class F>void query(int n,V q,double radius2,F& f)const{if(n<0)return;const KNode& nd=nodes[n];const Ray& rr=rays[nd.ray];V delta=sub(rr.u,q);if(dot(delta,delta)<=radius2)f(rr);double d=delta[nd.axis];if(d>=0){query(nd.left,q,radius2,f);if(d*d<=radius2)query(nd.right,q,radius2,f);}else{query(nd.right,q,radius2,f);if(d*d<=radius2)query(nd.left,q,radius2,f);}}
};
struct Node {double lo[6],hi[6];int parent=-1,left=-1,right=-1,status=0,lower=0;};
// Counts per budget: possible, definite, definitely passing, possibly nonpassing.
struct Counts {int64_t n=0,m=0,k=0,h=0;};
Counts plus(Counts a,Counts b,int sign=1){return {a.n+sign*b.n,a.m+sign*b.m,a.k+sign*b.k,a.h+sign*b.h};}
bool excludes(Counts c,int64_t qn,int64_t qd){if(c.m<8)return false;return c.k*qd>qn*c.n || std::max<int64_t>(0,c.m-c.h)*qd>qn*c.m;}
struct Boxes {V center,inner,outer,o;M r;bool resolved;};
Boxes boxes(const Node& node,V extent,V anchor,M road,V origin){double m[6],h[6];for(int i=0;i<6;i++){m[i]=(node.lo[i]+node.hi[i])/2;h[i]=(node.hi[i]-node.lo[i])/2;}M r=rot(m[3],m[4],m[5]);V e=extent;for(double& x:e)x+=.03;double p=m[3],roll=m[5];V axes[3]={{sin(p),-sin(roll)*cos(p),cos(roll)*cos(p)},{0,cos(roll),sin(roll)},{1,0,0}};double widths[3]={h[4],h[3],h[5]};M result=eye();for(int k=0;k<3;k++){V u=axes[k];double w=widths[k];M cross={0,-u[2],u[1],u[2],0,-u[0],-u[1],u[0],0};M f=eye();double sine=w>=M_PI/2?1:sin(w),versine=w>=M_PI?2:1-cos(w);for(int i=0;i<3;i++)for(int j=0;j<3;j++)f[3*i+j]+=sine*std::abs(cross[3*i+j])+versine*std::abs(u[i]*u[j]-(i==j));result=mm(result,f);}M delta{},rr=mm(trans(r),road);for(int i=0;i<3;i++)for(int j=0;j<3;j++)delta[3*i+j]=std::max(0.,result[3*i+j]-(i==j))+1e-14;V shift{};for(int i=0;i<3;i++)for(int j=0;j<3;j++)shift[i]+=std::abs(rr[3*i+j])*h[j];V out=add(add(e,mv(delta,e)),shift),in=sub(sub(e,mv(trans(delta),add(e,shift))),shift);for(int i=0;i<3;i++){out[i]+=1e-7;in[i]-=1e-7;}V center=add(anchor,mv(road,{m[0],m[1],m[2]}));V o=mv(trans(r),sub(origin,center));bool sensor_inside=true,resolved=true;for(int i=0;i<3;i++){if(in[i]<=0)resolved=false;if(std::abs(o[i])>out[i])sensor_inside=false;}return {center,in,out,o,r,resolved&&!sensor_inside};}
bool interval(V o,V d,V extent,double oz,double dz,double& leave){double lo=0,hi=std::numeric_limits<double>::infinity();for(int i=0;i<3;i++){if(std::abs(d[i])<=1e-12){if(std::abs(o[i])>extent[i])return false;}else{double a=(-extent[i]-o[i])/d[i],b=(extent[i]-o[i])/d[i];lo=std::max(lo,std::min(a,b));hi=std::min(hi,std::max(a,b));}}if(dz>1e-12)lo=std::max(lo,(.15-oz)/dz);else if(dz< -1e-12)hi=std::min(hi,(.15-oz)/dz);else if(oz<.15)return false;leave=hi;return hi>=lo&&lo<=1+1e-10;}
std::array<Counts,2> count(const Boxes& b,const Rays& rays){std::array<Counts,2> out{};if(!b.resolved)return out;M rt=trans(b.r);auto f=[&](const Ray& ray){V d=mv(rt,ray.d);double leave=0,dummy=0;bool possible=interval(b.o,d,b.outer,rays.origin[2],ray.d[2],leave),definite=interval(b.o,d,b.inner,rays.origin[2],ray.d[2],dummy);Counts c{possible,definite,definite&&leave<1-1e-10,possible&&leave>=1-1e-10};out[1]=plus(out[1],c);if(ray.stride==16)out[0]=plus(out[0],c);};V v=sub(b.center,rays.origin);double distance=norm(v),radius=norm(b.outer)+1e-7;if(distance<=radius){for(auto& r:rays.rays)f(r);}else{for(double& x:v)x/=distance;double cosine=sqrt(std::max(0.,1-(radius/distance)*(radius/distance)));double chord=sqrt(std::max(0.,2*(1-cosine)))+1e-10;rays.query(rays.root,v,chord*chord,f);}return out;}
int lower(const Node& n,double qx,double qy,int64_t radius){double x=std::max({n.lo[0]-qx,qx-n.hi[0],0.}),y=std::max({n.lo[1]-qy,qy-n.hi[1],0.});return age(std::max<int64_t>(0,int64_t(floor(x*1e6-1e-7))),std::max<int64_t>(0,int64_t(floor(y*1e6-1e-7))),radius);}
struct Context {V extent,anchor,origin;M road;double qx,qy;int64_t radius,qn,qd;int outside_lower,outside_upper;std::vector<Node> nodes;std::vector<std::array<Counts,2>> counts;std::vector<Boxes> geometries;double elapsed=0;int inspected=0;
 Context(const double* e,const double* a,const double* r,const double* o,double x,double y,int64_t rad,int64_t num,int64_t den):qx(x),qy(y),radius(rad),qn(num),qd(den){std::copy(e,e+3,extent.begin());std::copy(a,a+3,anchor.begin());std::copy(r,r+9,road.begin());std::copy(o,o+3,origin.begin());double dist=std::max(0.,std::min({qx+12,12-qx,qy+8,8-qy}));outside_lower=age(std::max<int64_t>(0,int64_t(floor(dist*1e6-1e-7))),0,radius);int64_t d=ceil(dist*1e6+1e-7);outside_upper=!safe(d,0,radius,0)?0:safe(d,0,radius,500000)?500000:age(d,0,radius)+1;}
};
extern "C" {
void* build(const double* e,const double* a,const double* road,const double* origin,double qx,double qy,int64_t radius,int64_t qn,int64_t qd,const double* points,const int* stride,int nrays,int budget){try{if(budget<1||budget>1000000||radius<0||radius>10000000||qn<0||qd<=0||qn>qd||nrays<0)return nullptr;auto begin=std::chrono::steady_clock::now();Context* c=new Context(e,a,road,origin,qx,qy,radius,qn,qd);Rays rays(points,stride,nrays,c->origin);Node root{};double pi=M_PI;double lo[6]={-12,-8,e[2]-.1,-pi/90,0,-pi/90},hi[6]={12,8,e[2]+.1,pi/90,2*pi,pi/90};std::copy(lo,lo+6,root.lo);std::copy(hi,hi+6,root.hi);root.lower=lower(root,qx,qy,radius);c->nodes.reserve(2*budget+1);c->nodes.push_back(root);using Q=std::pair<int,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> queue;queue.push({root.lower,0});c->counts.resize(1);c->geometries.resize(1);V padded=c->extent;for(double& x:padded)x+=.03;double body=norm(padded);
 while(!queue.empty()&&c->inspected<budget){int i=queue.top().second;queue.pop();c->inspected++;Node& n=c->nodes[i];if(n.lower>=c->outside_upper-1){n.status=3;continue;}Boxes b=boxes(n,c->extent,c->anchor,c->road,c->origin);auto cc=count(b,rays);c->counts[i]=cc;c->geometries[i]=b;if(excludes(cc[0],qn,qd)||excludes(cc[1],qn,qd)){n.status=2;continue;}if(c->inspected==budget){n.status=4;break;}int axis=0;double weight=-1;for(int j=0;j<6;j++){double h=(n.hi[j]-n.lo[j])/2;double w=j<3?h:2*body*sin(std::min(h,pi)/2);if(w>weight){weight=w;axis=j;}}double mid=(n.lo[axis]+n.hi[axis])/2;Node left=n,right=n;left.hi[axis]=mid;right.lo[axis]=mid;left.parent=right.parent=i;left.status=right.status=0;left.lower=lower(left,qx,qy,radius);right.lower=lower(right,qx,qy,radius);n.status=1;n.left=c->nodes.size();n.right=n.left+1;int j=n.left;c->nodes.push_back(left);c->nodes.push_back(right);c->counts.resize(c->nodes.size());c->geometries.resize(c->nodes.size());queue.push({left.lower,j});queue.push({right.lower,j+1});}
 c->elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();return c;}catch(...){return nullptr;}}
int size(void* ptr){return static_cast<Context*>(ptr)->nodes.size();}
// Export proof records, including all counts from evaluated cells.
void export_nodes(void* ptr,double* cells,int64_t* meta,int64_t* counts){auto c=static_cast<Context*>(ptr);for(size_t i=0;i<c->nodes.size();i++){auto& n=c->nodes[i];for(int j=0;j<6;j++){cells[12*i+j]=n.lo[j];cells[12*i+6+j]=n.hi[j];}int64_t v[6]={n.parent,n.left,n.right,n.status,n.lower,0};std::copy(v,v+6,meta+6*i);for(int s=0;s<2;s++){auto cc=c->counts[i][s];int64_t v2[4]={cc.n,cc.m,cc.k,cc.h};std::copy(v2,v2+4,counts+8*i+4*s);}}}
void stats(void* ptr,double* out){auto c=static_cast<Context*>(ptr);int l=c->outside_lower,excluded=0;for(auto& n:c->nodes){if(n.status==2)excluded++;else if(n.status!=1)l=std::min(l,n.lower);}out[0]=l;out[1]=c->outside_upper;out[2]=c->elapsed;out[3]=excluded;out[4]=c->inspected;}
// Query SAME inherited partition. Unchecked leaves always remain possible.
// delta inputs contain all changed old/new rays; rebuild inputs contain all current rays.
void revalidate(void* ptr,const double* oldp,const int* olds,int oldn,const double* newp,const int* news,int newn,int delta,int64_t* outcounts,int* accepted,double* stat){auto begin=std::chrono::steady_clock::now();auto c=static_cast<Context*>(ptr);Rays oldr(oldp,olds,oldn,c->origin),newr(newp,news,newn,c->origin);int lower_us=c->outside_lower,excluded=0,revoked=0;
 for(size_t i=0;i<c->nodes.size();i++){const Node& n=c->nodes[i];if(n.status==1){accepted[i]=-1;continue;}bool reject=false;std::array<Counts,2> cc{};
 if(n.status==2){cc=count(c->geometries[i],newr);if(delta){auto minus=count(c->geometries[i],oldr);for(int s=0;s<2;s++)cc[s]=plus(plus(c->counts[i][s],minus[s],-1),cc[s]);}reject=excludes(cc[0],c->qn,c->qd)||excludes(cc[1],c->qn,c->qd);if(!reject)revoked++;}
 accepted[i]=reject?1:0;if(reject)excluded++;else lower_us=std::min(lower_us,n.lower);for(int s=0;s<2;s++){int64_t v[4]={cc[s].n,cc[s].m,cc[s].k,cc[s].h};std::copy(v,v+4,outcounts+8*i+4*s);}}
 stat[0]=lower_us;stat[1]=c->outside_upper;stat[2]=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();stat[3]=excluded;stat[4]=revoked;}
void destroy(void* p){delete static_cast<Context*>(p);}
int exact_age(int64_t x,int64_t y,int64_t r){if(x<0||y<0||x>100000000||y>100000000||r<0||r>10000000)return -1;return age(x,y,r);}
}
