// Independent world-halfspace reference. No native solver/index/enclosure code.
#include <cmath>
#include <cstdint>
#include <limits>
extern "C" void reference_counts(const double* pts,const int64_t* ids,int n,const double* origin,const double* normals,const double* small,const double* large,int64_t* out){
 for(int k=0;k<8;k++)out[k]=0;
 double slack[2][7];for(int b=0;b<2;b++)for(int j=0;j<7;j++)slack[b][j]=(b==0?small[j]:large[j])-(normals[3*j]*origin[0]+normals[3*j+1]*origin[1]+normals[3*j+2]*origin[2]);
 for(int index=0;index<n;index++){int64_t i=ids[index];bool eligible[2];double exits[2];double dx=pts[3*i]-origin[0],dy=pts[3*i+1]-origin[1],dz=pts[3*i+2]-origin[2];for(int b=0;b<2;b++){double entry=0,exit=std::numeric_limits<double>::infinity();bool valid=true;for(int j=0;j<7;j++){double d=normals[3*j]*dx+normals[3*j+1]*dy+normals[3*j+2]*dz;if(std::abs(d)<=1e-12){if(slack[b][j]<0)valid=false;}else{double t=slack[b][j]/d;if(d<0){if(t>entry)entry=t;}else{if(t<exit)exit=t;}}}eligible[b]=valid&&exit>=entry&&entry<=1+1e-10;exits[b]=exit;}
 int64_t c[4]={eligible[1],eligible[0],eligible[0]&&exits[1]<1-1e-10,eligible[1]&&exits[1]>=1-1e-10};for(int k=0;k<4;k++){out[4+k]+=c[k];if(i%4==0)out[k]+=c[k];}
 }
}
