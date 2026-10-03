#!/usr/bin/env python3
"""Independent full-ray exclusions, continuous partition and collision witnesses."""
import argparse,gzip,hashlib,importlib.util,json,math,struct,zlib
from decimal import Decimal,localcontext,ROUND_CEILING
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('independent_faces',ROOT/'experiments/shape_evidence_20261002/audit.py');face_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(face_module)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotation(angles):
    p,y,r=angles
    rx=np.array([[1,0,0],[0,math.cos(r),math.sin(r)],[0,-math.sin(r),math.cos(r)]])
    ry=np.array([[math.cos(p),0,-math.sin(p)],[0,1,0],[math.sin(p),0,math.cos(p)]])
    rz=np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]])
    return rz@ry@rx
def contact(dx,dy,radius):
    with localcontext() as c:
        c.prec=70;clearance=Decimal(int(dx)**2+int(dy)**2).sqrt()-int(radius)-750000
        if clearance<=0:return (0,0)
        v=Decimal(5000000);a=Decimal(3000000);t=2*clearance/(v+(v*v+2*a*clearance).sqrt());first=int((t*1000000).to_integral_value(rounding=ROUND_CEILING));safe=min(500000,first-1);return safe,min(500000,first)
def frac(s):return Fraction(s['numerator'],s['denominator'])
def face_events(points,origin,center,r,ext):
    o=(origin-center)@r;d=(points-origin)@r;events=[]
    for axis in range(3):
        other=[i for i in range(3) if i!=axis]
        for sign in (-1,1):
            moving=abs(d[:,axis])>1e-12;t=np.divide(sign*ext[axis]-o[axis],d[:,axis],out=np.zeros(len(d)),where=moving);cross=o[other]+t[:,None]*d[:,other];valid=moving&np.all(abs(cross)<=ext[other]+1e-10,axis=1);events.append(np.where(valid,t,np.nan))
    ev=np.array(events);entry=np.min(np.where(np.isnan(ev),np.inf,ev),axis=0);leave=np.max(np.where(np.isnan(ev),-np.inf,ev),axis=0);eligible=(leave>=np.maximum(entry,0))&(entry<=1+1e-10)&(leave>=0);return eligible,leave
def boxes(node,extent,anchor,road,refined):
    lo=np.array(node['lo']);hi=np.array(node['hi']);m=(lo+hi)/2;h=(hi-lo)/2;r=rotation(m[3:]);e=np.array(extent)+.03;shift=np.abs(r.T@road)@h[:3]
    if not refined:
        turn=2*np.linalg.norm(e)*math.sin(min(math.pi,sum(h[3:]))/2);inner=e-shift-turn-1e-7;outer=e+shift+turn+1e-7
    else:
        p,y,roll=m[3:];u=[np.array([math.sin(p),-math.sin(roll)*math.cos(p),math.cos(roll)*math.cos(p)]),np.array([0,math.cos(roll),math.sin(roll)]),np.array([1.,0.,0.])];ee=[]
        for axis,w in zip(u,[h[4],h[3],h[5]]):
            x,y0,z=axis;k=np.array([[0,-z,y0],[z,0,-x],[-y0,x,0.]]);s=1 if w>=math.pi/2 else math.sin(w);c=2 if w>=math.pi else 1-math.cos(w);ee.append(s*abs(k)+c*abs(np.outer(axis,axis)-np.eye(3)))
        a,b,c=ee;d=a+b+c+a@b+a@c+b@c+a@b@c+1e-14;inner=e-d.T@(e+shift)-shift-1e-7;outer=e+d@e+shift+1e-7
    return np.array(anchor)+road@m[:3],r,inner,outer
def footprint_distance(pose,extent,road,query):
    corners=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)]);xy=((corners*np.asarray(extent))@(road.T@rotation(pose[3:])).T+pose[:3])[:,:2];h=ConvexHull(xy);polygon=xy[h.vertices];q=np.asarray(query)
    if np.all(h.equations[:,:2]@q+h.equations[:,2]<=1e-10):return 0.
    answer=float('inf')
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        v=b-a;t=np.clip(np.dot(q-a,v)/np.dot(v,v),0,1);answer=min(answer,float(np.linalg.norm(q-a-t*v)))
    return answer
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();allrows=[];packets={};packetchecks=0;nodechecks=0;exclusions=0;fullraychecks=0;truthrecords=[];agecache={};witnessbank=[]
    catalog=json.loads((HERE/'catalog.json').read_bytes());bps=sorted(catalog)
    for variant in ('replay','refined'):
        directory=a.results/variant;manifest=json.loads((directory/'manifest.json').read_bytes());rows=json.loads((directory/'rows.json').read_bytes());sources=json.loads((directory/'sources.json').read_bytes());assert len(rows)==manifest['calls']==144;assert len(sources)==12;srcs={s['case']:s for s in sources};assert sha(HERE/'PROTOCOL.md')==manifest['protocol_sha256'];assert sha(HERE/'source_manifest.json')==manifest['source_manifest_sha256']
        if variant=='refined':assert sha(HERE/'PROTOCOL_REFINED.md')==manifest['refinement_protocol_sha256'];assert sha(HERE/'refinement_manifest.json')==manifest['refinement_manifest_sha256']
        for source in sources:
            assert source['status']=='available';assert sha(ROOT/source['source_cloud'])==source['source_cloud_sha256'];assert sha(ROOT/source['source_record'])==source['source_record_sha256'];assert sha(ROOT/source['calibration_analysis'])==source['calibration_sha256'];actual=json.loads((ROOT/source['calibration_analysis']).read_bytes())['summary'][source['blueprint']]['joint']['threshold'];assert actual==source['threshold'];assert source['extent']==catalog[source['blueprint']]['extent']
            rr=json.loads((ROOT/source['source_record']).read_bytes());truth=next(r for r in rr if r.get('id')==source['source_id']);road=np.array(source['road_rotation']);pose=np.r_[road.T@(np.array(truth['center'])-source['anchor']),np.deg2rad(truth['actor_transform']['rotation'])];pose[4]%=2*math.pi;extent=source['extent'];lower=np.array([-12,-8,extent[2]-.1,math.radians(-2),0,math.radians(-2)]);upper=np.array([12,8,extent[2]+.1,math.radians(2),2*math.pi,math.radians(2)]);fits=bool(np.all(pose>=lower)&np.all(pose<=upper));truthrecords.append(dict(variant=variant,case=source['case'],pose=[round(float(x),12) for x in pose],inside_declared_domain=fits,extent_matches=truth['bounding_box']['extent']==extent))
        for row in rows:
            source=srcs[row['case']];packetkey=(variant,row['case'],row['stride']);extent=source['extent'];anchor=np.array(source['anchor']);road=np.array(source['road_rotation']);q=frac(source['threshold'])
            if packetkey not in packets:
                payload=zlib.decompress((directory/row['packet_file']).read_bytes());assert len(payload)==row['wire_bytes'] and hashlib.sha256(payload).hexdigest()==row['packet_sha256'];assert hashlib.sha256(payload[:-32]).digest()==payload[-32:];header=struct.Struct('<4sHHIIHHd16d32sI');v=header.unpack(payload[:header.size]);assert v[:2]==(b'PIV1',1);assert v[2]==bps.index(source['blueprint']);assert v[3]==source['source_frame'] and v[5]==row['stride'] and v[6]==0 and v[7]==source['source_timestamp'];assert v[24].hex()==source['calibration_sha256'];n=v[25];assert n==(v[4]+v[5]-1)//v[5];assert len(payload)==header.size+12*n+32;raw=np.frombuffer(payload,dtype='<f4',count=n*3,offset=header.size).reshape(n,3);matrix=np.array(v[8:24]).reshape(4,4)
                with np.load(ROOT/source['source_cloud']) as z:
                    original=np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']];assert len(original)==v[4];np.testing.assert_array_equal(raw,original[::v[5]]);np.testing.assert_array_equal(matrix,z['transform']);assert float(z['timestamp'])==v[7]
                world=raw.astype(float)@matrix[:3,:3].T+matrix[:3,3];views=[world[::s//row['stride']] for s in (16,4,1) if s>=row['stride']];packets[packetkey]=(views,matrix[:3,3]);packetchecks+=1
            views,origin=packets[packetkey];f=directory/row['tree_file'];assert sha(f)==row['tree_sha256'];tree=json.loads(gzip.decompress(f.read_bytes()));assert tree['policy']==row['policy'] and tree['max_nodes']==2000;assert tree['cap_us']==500000;assert tree['query_xy']==[(-6 if row['query_index']==0 else 6),0];query=np.array(tree['query_xy']);radius=math.ceil(float(np.linalg.norm(extent))*1e6);assert tree['body_radius_um']==radius and tree['query_radius_um']==750000 and tree['speed_um_s']==5000000 and tree['acceleration_um_s2']==3000000;assert frac(tree['threshold'])==q;nodes=tree['nodes'];assert nodes[0]['parent'] is None;assert nodes[0]['lo']==[-12.,-8.,extent[2]-.1,math.radians(-2),0.,math.radians(-2)];assert nodes[0]['hi']==[12.,8.,extent[2]+.1,math.radians(2),2*math.pi,math.radians(2)];children=[];retained=[]
            for i,node in enumerate(nodes):
                assert node['id']==i;lo=np.array(node['lo']);hi=np.array(node['hi']);assert np.all(lo<=hi) and np.isfinite(lo).all() and np.isfinite(hi).all();key=(tuple(lo[:2]),tuple(hi[:2]),tuple(query),radius)
                if key not in agecache:
                    d=np.maximum(np.maximum(lo[:2]-query,query-hi[:2]),0);du=np.maximum(np.floor(d*1e6-1e-7),0).astype(np.int64);agecache[key]=contact(*du,radius)[0]
                assert node['lower_us']==agecache[key];nodechecks+=1
                if node['status']=='split':
                    ia,ib=node['children'];assert i<ia<ib<len(nodes);left,right=nodes[ia],nodes[ib];assert left['parent']==right['parent']==i and left['lo']==node['lo'] and right['hi']==node['hi'];changed=[j for j in range(6) if left['hi'][j]!=node['hi'][j]];assert len(changed)==1;j=changed[0];assert left['hi'][j]==right['lo'][j]==(lo[j]+hi[j])/2;assert all(left['hi'][k]==node['hi'][k] and right['lo'][k]==node['lo'][k] for k in range(6) if k!=j);children.extend((ia,ib))
                elif node['status']=='excluded':
                    decisive=next(j for j,b in enumerate(node['bounds']) if frac(b)>q);tested=node['bounds'][decisive];center,r,inner,outer=boxes(node,extent,anchor,road,variant=='refined');assert min(inner)>0 and not np.all(abs((origin-center)@r)<=outer);possible,leave=face_events(views[decisive],origin,center,r,outer);definite,_=face_events(views[decisive],origin,center,r,inner);n=int(possible.sum());support=int(definite.sum());passing=int(np.sum(definite&(leave<1-1e-10)));hits=int(np.sum(possible&(leave>=1-1e-10)));assert support>=8;assert (n,support,passing)==(tested['possibly_eligible'],tested['definitely_eligible'],tested['definitely_passed']);b=Fraction(passing,n)
                    if variant=='refined':assert hits==tested['possibly_nonpassing'];b=max(b,Fraction(max(0,support-hits),support))
                    assert b==frac(tested) and b>q;exclusions+=1;fullraychecks+=len(views[decisive])
                else:assert node['status'] in ('pending','time_retained','budget_retained','witness_retained');retained.append(node['lower_us'])
            assert sorted(children)==list(range(1,len(nodes)));assert len(retained)==tree['retained_leaves'];assert sum(n['status']=='excluded' for n in nodes)==tree['excluded_leaves'];assert sum(n['status']!='pending' for n in nodes)==tree['examined_nodes']<=2000
            distance=max(0,min(query[0]+12,12-query[0],query[1]+8,8-query[1]));ol=contact(max(0,math.floor(distance*1e6-1e-7)),0,radius)[0];ou=contact(math.ceil(distance*1e6+1e-7),0,radius)[1];assert ol==tree['outside_lower_us'];assert min([ol]+retained)==tree['lower_us'];w=tree['witness'];extra={}
            if w['kind']=='retained_pose':
                pose=np.array(w['pose']);assert np.all(pose>=nodes[0]['lo']) and np.all(pose<=nodes[0]['hi']);center=anchor+road@pose[:3];r=rotation(pose[3:]);scores=[face_module.reference(v,origin,center,r,extent) for v in views];assert scores==w['scores'];assert all(frac(s)<=q for s in scores);du=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);assert du==w['distance_upper_um'];assert contact(du,0,radius)[1]==w['upper_us'];dist=footprint_distance(pose,extent,road,query);extra=dict(footprint_distance_m=round(dist,10),bounding_box_footprint_overlaps_task=dist<=.75+1e-9);witnessbank.append(dict(variant=variant,case=row['case'],query_index=row['query_index'],stride=row['stride'],policy=row['policy'],pose=pose.tolist(),upper_us=w['upper_us'],**extra))
            else:assert w['kind']=='unknown_boundary' and w['upper_us']==ou
            assert tree['upper_us']==w['upper_us'];assert 0<=tree['lower_us']<=tree['upper_us']<=500000;assert tree['gap_us']==tree['upper_us']-tree['lower_us']
            for k in ('lower_us','upper_us','gap_us','examined_nodes','excluded_leaves','retained_leaves'):assert row[k]==tree[k]
            assert row['receiver_ns']>=row['decode_index_ns']>=0;age=math.ceil((row['encoder_ns']+row['receiver_ns'])/1000+20000+row['wire_bytes']*8/20000000*1e6);assert row['modeled_age_us']==age;assert row['usable_lower_us']==max(0,row['lower_us']-age-20000-200000);assert row['source_timestamp']==source['source_timestamp'];assert row['virtual_ready_timestamp']==row['source_timestamp']+age/1e6
            allrows.append(dict(variant=variant,id=row['id'],case=row['case'],query_index=row['query_index'],stride=row['stride'],policy=row['policy'],lower_us=row['lower_us'],upper_us=row['upper_us'],**extra))
        print('audited',variant,len(rows),flush=True)
    result=dict(calls=len(allrows),packet_checks=packetchecks,tree_nodes=nodechecks,full_ray_exclusions=exclusions,full_ray_exclusion_checks=fullraychecks,truth_domain=truthrecords,rows=allrows,witness_bank=witnessbank,scope='Exact root partition and full-ray proof/witness checks for the declared score/disc abstraction. Upright operating domain, calibration exchangeability and physical bbox/dynamics validity remain assumptions; a bbox overlap is not a mesh collision.',auditor_sha256=sha(Path(__file__)),face_reference_sha256=sha(ROOT/'experiments/shape_evidence_20261002/audit.py'))
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','witness_bank','truth_domain','scope')}))
if __name__=='__main__':main()
