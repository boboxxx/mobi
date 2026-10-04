"""Observed XYZ frontend and immutable provenance; truth only for qualification."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from scores import ROOT
from inference import groups
from kernel import hull
E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def freeze_check():
    for filename in ('freeze.json','measurement_freeze.json'):
        f=read(E/filename)
        for section in ('sources','inputs'):
            for n,h in f[section].items():assert sha(ROOT/n)==h,n
def load(r):
    path=P/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
    with np.load(path) as z:raw=z['raw'];T=z['transform'].copy();assert float(z['timestamp'])==r['timestamp']
    return raw,T,path
def frontend(raw,T,extent,basis,background,layout):
    xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');gg=groups(xyz,T,np.asarray(basis['anchor']),np.asarray(basis['road']),extent,background['layouts'][str(layout)]['codes']);return gg,[hull(g) for g in gg]
def observed_record(r,catalog,basis,background):
    raw,T,path=load(r);ext=catalog[r['blueprint']];assert r['bounding_box']['extent']==ext and r['bounding_box']['rotation']==[0.,0.,0.]
    assert np.allclose(r['query'],basis['anchor'][:2],rtol=0,atol=0);yaw=math.radians(r['road_yaw']);road=[[math.cos(yaw),-math.sin(yaw),0.],[math.sin(yaw),math.cos(yaw),0.],[0.,0.,1.]];assert road==basis['road']
    gg,hh=frontend(raw,T,ext,basis,background,r['layout']);xy=(np.asarray(r['center'])-basis['anchor'])@np.asarray(basis['road'])
    return dict(**r,groups_cm=gg,hulls_cm=hh,true_xy=xy[:2].tolist(),source_us=math.floor(r['timestamp']*1e6),acquisition_us=math.ceil(r['acquisition_s']*1e6))
