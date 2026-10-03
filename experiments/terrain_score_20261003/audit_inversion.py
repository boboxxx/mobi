#!/usr/bin/env python3
"""Independent all-leaf partition, full-ray exclusion, witness and age audit."""
import argparse,gzip,hashlib,importlib.util,json,math,struct,zlib
from fractions import Fraction
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('independent_pose_audit',ROOT/'experiments/pose_inversion_20261003/audit.py');terrain=load('independent_terrain_audit',HERE/'audit.py')
def events(points,origin,center,rotation,ext):
    normals=np.concatenate([rotation.T,-rotation.T,[[0,0,-1]]]);offset=np.r_[rotation.T@center+ext,-rotation.T@center+ext,-.15];lo=np.zeros(len(points));hi=np.full(len(points),np.inf);valid=np.ones(len(points),bool)
    for n,b in zip(normals,offset-normals@origin):
        d=(points-origin)@n;up=d>1e-12;down=d< -1e-12;flat=~(up|down);valid&=~flat|(b>=0);cross=np.divide(b,d,out=np.zeros(len(points)),where=~flat);lo=np.maximum(lo,np.where(down,cross,-np.inf));hi=np.minimum(hi,np.where(up,cross,np.inf))
    return valid&(hi>=lo)&(lo<=1+1e-10),hi

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--variant',default='inversion');ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();directory=a.results/a.variant;analysis=json.loads((a.results/'analysis_sheng.json').read_bytes());manifest=json.loads((directory/'manifest.json').read_bytes());digest=hashlib.sha256((a.results/'analysis_sheng.json').read_bytes()).hexdigest();assert manifest['analysis_sha256']==digest
    for path,sha in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};rows=json.loads((directory/'rows.json').read_bytes());assert len(rows)==24;nodecount=0;excluded=0;raychecks=0;witnesses=0;packetcache={};agecache={}
    for row in rows:
        s=sources[row['case']];ext=np.array(s['extent']);anchor=np.array(s['anchor']);road=np.array(s['road_rotation']);q=Fraction(**analysis['summary'][s['blueprint']]['threshold']);wire=zlib.decompress((directory/row['packet_file']).read_bytes());assert len(wire)==row['wire_bytes'] and hashlib.sha256(wire).hexdigest()==row['packet_sha256'];assert hashlib.sha256(wire[:-32]).digest()==wire[-32:]
        if row['case'] not in packetcache:
            header=struct.Struct('<4sHHIIHHd16d32sI');h=header.unpack(wire[:header.size]);assert h[:2]==(b'PIV1',1) and h[3]==s['source_frame'] and h[5]==4 and h[7]==s['source_timestamp'] and h[24].hex()==digest;matrix=np.array(h[8:24]).reshape(4,4);xyz=np.frombuffer(wire,dtype='<f4',offset=header.size,count=h[25]*3).reshape(-1,3)
            with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];np.testing.assert_array_equal(xyz,np.c_[raw['x'],raw['y'],raw['z']][::4]);np.testing.assert_array_equal(matrix,z['transform']);assert h[4]==len(raw)
            points=xyz.astype(float)@matrix[:3,:3].T+matrix[:3,3];packetcache[row['case']]=([points[::4],points],matrix[:3,3])
        views,origin=packetcache[row['case']];blob=(directory/row['tree_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==row['tree_sha256'];tree=json.loads(gzip.decompress(blob));assert tree['max_nodes']==manifest['max_nodes'] and tree['query_xy']==[(-6 if row['query_index']==0 else 6),0];nodes=tree['nodes'];query=np.array(tree['query_xy']);radius=math.ceil(float(np.linalg.norm(ext))*1e6);assert radius==tree['body_radius_um'];assert nodes[0]['lo']==[-12.,-8.,ext[2]-.1,math.radians(-2),0.,math.radians(-2)] and nodes[0]['hi']==[12.,8.,ext[2]+.1,math.radians(2),2*math.pi,math.radians(2)];parents=[];retained=[]
        for i,node in enumerate(nodes):
            assert node['id']==i;lo=np.array(node['lo']);hi=np.array(node['hi']);assert np.all(lo<=hi);nodecount+=1;key=(tuple(lo[:2]),tuple(hi[:2]),tuple(query),radius)
            if key not in agecache:
                d=np.maximum(np.maximum(lo[:2]-query,query-hi[:2]),0);u=np.maximum(np.floor(d*1e6-1e-7),0).astype(np.int64);agecache[key]=old.contact(*u,radius)[0]
            assert node['lower_us']==agecache[key]
            if node['status']=='split':
                aa,bb=[nodes[j] for j in node['children']];assert aa['parent']==bb['parent']==i;parents+=node['children'];l=np.array(aa['lo']);h=np.array(aa['hi']);l2=np.array(bb['lo']);h2=np.array(bb['hi']);np.testing.assert_array_equal(l,lo);np.testing.assert_array_equal(h2,hi);axis=np.flatnonzero(h!=hi);assert len(axis)==1;j=axis[0];assert h[j]==l2[j] and lo[j]<h[j]<hi[j];np.testing.assert_array_equal(np.delete(h,j),np.delete(hi,j));np.testing.assert_array_equal(np.delete(l2,j),np.delete(lo,j))
            elif node['status']=='excluded':
                center,r,inner,outer=old.boxes(node,ext,anchor,road,True);assert np.all(inner>0);verified=False
                for p,b in zip(views,node['bounds']):
                    if Fraction(b['numerator'],b['denominator'])<=q:continue
                    possible,leave=events(p,origin,center,r,outer);definite,_=events(p,origin,center,r,inner);n=int(possible.sum());m=int(definite.sum());k=int(np.sum(definite&(leave<1-1e-10)));hits=int(np.sum(possible&(leave>=1-1e-10)));assert m>=8;lb=max(Fraction(k,n),Fraction(max(0,m-hits),m));assert lb==Fraction(b['numerator'],b['denominator']) and lb>q;verified=True;raychecks+=len(p)
                assert verified;excluded+=1
            else:retained.append(node['lower_us'])
        assert sorted(parents)==list(range(1,len(nodes)))
        boundary=min(query[0]+12,12-query[0],query[1]+8,8-query[1]);outlo,outup=old.contact(max(0,math.floor(boundary*1e6-1e-7)),0,radius);_,outup2=old.contact(math.ceil(boundary*1e6+1e-7),0,radius);assert tree['outside_lower_us']==outlo;assert tree['lower_us']==row['lower_us']==min([outlo]+retained)
        w=tree['witness']
        if w['kind']=='retained_pose':
            pose=np.array(w['pose']);center=anchor+road@pose[:3];r=old.rotation(pose[3:]);assert np.all(pose>=nodes[0]['lo']) and np.all(pose<=nodes[0]['hi'])
            for p,ss in zip(views,w['scores']):
                n,k,nu,de=terrain.reference(p,origin,center,r,ext);assert (n,k,nu,de)==(ss['visible_count'],ss['pass_count'],ss['numerator'],ss['denominator']);assert Fraction(nu,de)<=q
            du=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);assert old.contact(du,0,radius)[1]==tree['upper_us'];witnesses+=1
        else:assert w['kind']=='unknown_boundary' and tree['upper_us']==outup2
        assert row['upper_us']==tree['upper_us'] and row['excluded_cells']==sum(n['status']=='excluded' for n in nodes)
    a.out.write_text(json.dumps(dict(calls=len(rows),packet_checks=len(packetcache),nodes=nodecount,whole_cell_exclusions=excluded,full_ray_exclusion_point_checks=raychecks,retained_witnesses=witnesses,positive_lower=sum(r['lower_us']>0 for r in rows),zero_upper=sum(r['upper_us']==0 for r in rows),rows_sha256=hashlib.sha256((directory/'rows.json').read_bytes()).hexdigest(),audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
