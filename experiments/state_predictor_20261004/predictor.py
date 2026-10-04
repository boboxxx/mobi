"""Hull-only fixed baselines. No truth or future fields enter inference."""
import math
import numpy as np

METHODS=('bbox','ridge','quadratic')
def features(hulls,layout):
    if not hulls:return None,None
    parts=[]
    for h in hulls:
        p=np.asarray(h,dtype=np.float64)/100.;lo=p.min(0);hi=p.max(0);mean=p.mean(0);span=hi-lo
        area=abs(float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))))/2
        parts.append((area,len(h),tuple(lo),p,lo,hi,mean,span))
    parts.sort(key=lambda a:(-a[0],-a[1],a[2]));anchor=(parts[0][4]+parts[0][5])/2
    f=[float(layout),len(hulls),float(anchor[0]),float(anchor[1])]
    for i in range(3):
        if i>=len(parts):f.extend([0.]*12);continue
        area,n,_,p,lo,hi,mean,span=parts[i];centred=p-mean
        cov=centred.T@centred/len(p)
        f.extend([1.,math.log1p(n),area,*(mean-anchor),*span,cov[0,0],cov[1,1],cov[0,1],float(np.mean(centred[:,0]**3)),float(np.mean(centred[:,1]**3))])
    assert len(f)==40
    return np.asarray(f),anchor

def design(z,method):
    if method=='quadratic':z=np.c_[z,z*z]
    return np.c_[np.ones(len(z)),z]

def fit(rows,labels,method):
    if method=='bbox':return dict(method=method)
    fs=[];ys=[]
    for r in rows:
        f,a=features(r['hulls_cm'],r['layout'])
        if f is None:continue
        fs.append(f);ys.append(np.asarray(labels[r['id']])-a)
    X=np.asarray(fs);Y=np.asarray(ys);mu=X.mean(0);sd=X.std(0);sd=np.maximum(sd,.001);Z=design((X-mu)/sd,method)
    penalty=np.eye(Z.shape[1])*(1. if method=='ridge' else 10.);penalty[0,0]=0
    w=np.linalg.solve(Z.T@Z+penalty,Z.T@Y)
    return dict(method=method,mean=mu.tolist(),scale=sd.tolist(),weights=w.tolist(),training_rows=len(X))

def predict(hulls,layout,model):
    f,a=features(hulls,layout)
    if f is None:return None
    if model['method']!='bbox':
        z=(f-np.asarray(model['mean']))/np.asarray(model['scale']);a=a+(design(z[None,:],model['method'])@np.asarray(model['weights']))[0]
    return [int(round(float(x)*1000000)) for x in a]
