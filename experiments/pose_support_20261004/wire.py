"""Same actual hull wire for all inference policies; existing XYZ wire for raw."""
import hashlib,json,math,struct,zlib
import numpy as np
from observer import projections,parameters,geometry,DIRECTIONS
from kernel import geometry as sphere_geometry
from frontend import groups
HEADER=struct.Struct('<4sBBIIq32s32s');RAW=struct.Struct('<4sIIdI32s32s')
POLICIES=('sphere_hull','pose_hull','joint_hull','joint_raw')

def infer(hulls,extent,slack,policy):
 p=parameters(extent,slack);s=None;o=None
 if policy in ('sphere_hull','joint_hull','joint_raw'):s=sphere_geometry(hulls,p['body_um']+8000+slack,p['body_um'])
 if policy!='sphere_hull':o=geometry(projections(hulls),p)
 if policy=='sphere_hull':return dict(status=s['status'],lower_us=[v['lower_us'] for v in s['queries']] if s['status']=='bounded' else [])
 if policy=='pose_hull':return dict(status=o['status'],lower_us=[v['lower_us'] for v in o['queries']] if o['status']=='bounded' else [])
 if any(v['status']=='empty' for v in (s,o)):return dict(status='empty',lower_us=[])
 bounded=[v for v in (s,o) if v['status']=='bounded']
 if not bounded:return dict(status='refused',lower_us=[])
 return dict(status='bounded',lower_us=[max(v['queries'][i]['lower_us'] for v in bounded) for i in (0,1)])

def unpack(wire,policy,context,contract,calibration):
 assert context['directions']==DIRECTIONS and context['tilt_operator_norm_upper']==[87267,1000000] and context['yaw_cell_distance_factor']==[8730,1000000]
 b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:];catalog=context['catalog'];slacks=context['slacks_um']
 if policy=='joint_raw':
  h=RAW.unpack(b[:RAW.size]);rc=context['raw_transport'];assert h[0]==b'RXYZ' and h[5].hex()==rc['contract'] and h[6].hex()==rc['calibration'];ci,frame,source=h[1],h[2],math.floor(h[3]*1e6);T=np.frombuffer(b,dtype='<f8',count=16,offset=RAW.size).reshape(4,4);assert len(b)==RAW.size+128+h[4]*12+32;xyz=np.frombuffer(b,dtype='<f4',count=h[4]*3,offset=RAW.size+128).reshape(-1,3);matches=[int(k) for k,v in rc['transforms'].items() if np.array_equal(T,v)];assert len(matches)==1;layout=matches[0];extent=catalog[list(catalog)[ci]];gg=groups(xyz,T,np.array(context['basis']['anchor']),np.array(context['basis']['road']),extent,context['background']['layouts'][str(layout)]['codes'])
 else:
  h=HEADER.unpack(b[:HEADER.size]);assert h[0]==b'BEX1' and h[1]==1 and h[6].hex()==contract and h[7].hex()==calibration;ci,layout,frame,source=h[3],h[2],h[4],h[5];gg=json.loads(b[HEADER.size:-32])
 assert 0<=ci<len(catalog) and layout in (0,1);bp=list(catalog)[ci];out=infer(gg,catalog[bp],slacks[bp],policy);return dict(**out,class_index=ci,frame=frame,source_us=source,layout=layout)
