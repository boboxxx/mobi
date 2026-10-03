#include "../expiry_runtime_20261003/kernel.cpp"
struct PointScorer {
 V extent,anchor,origin; M road; Rays rays;
 PointScorer(const double* p,const int* s,int n,const double* e,const double* a,const double* r,const double* o)
 :rays(p,s,n,V{o[0],o[1],o[2]}) {
  std::copy(e,e+3,extent.begin());std::copy(a,a+3,anchor.begin());
  std::copy(r,r+9,road.begin());std::copy(o,o+3,origin.begin());
 }
};
extern "C" {
void* scorer_create(const double* p,const int* s,int n,const double* e,const double* a,const double* r,const double* o){
 try{return new PointScorer(p,s,n,e,a,r,o);}catch(...){return nullptr;}
}
void scorer_evaluate(void* ptr,const double* poses,int n,int64_t* output){
 auto c=static_cast<PointScorer*>(ptr);V padded=c->extent;for(double& x:padded)x+=.03;
 for(int i=0;i<n;i++){
  const double* p=poses+6*i;Boxes b{};
  b.center=add(c->anchor,mv(c->road,V{p[0],p[1],p[2]}));b.r=rot(p[3],p[4],p[5]);
  b.inner=b.outer=padded;b.o=mv(trans(b.r),sub(c->origin,b.center));
  bool inside=true;for(int j=0;j<3;j++)inside&=std::abs(b.o[j])<=padded[j];
  b.resolved=!(inside&&c->origin[2]>=.15);
  auto counts=count(b,c->rays);
  for(int j=0;j<2;j++){output[i*4+j*2]=counts[j].n;output[i*4+j*2+1]=counts[j].k;}
 }
}
void scorer_destroy(void* ptr){delete static_cast<PointScorer*>(ptr);}
}
