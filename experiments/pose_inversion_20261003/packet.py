"""Actual geometry-only binary payload; fixed, nested return subsampling."""
import hashlib,struct
import numpy as np
HEADER=struct.Struct('<4sHHIIHHd16d32sI')
STRIDES=(16,4,1)
def encode(xyz,frame,timestamp,transform,stride,blueprint_index,calibration_sha256):
    if stride not in STRIDES:raise ValueError('Unsupported budget')
    xyz=np.asarray(xyz,dtype='<f4');matrix=np.asarray(transform,dtype=float)
    if xyz.ndim!=2 or xyz.shape[1]!=3 or matrix.shape!=(4,4):raise ValueError('Geometry shape')
    p=np.ascontiguousarray(xyz[::stride],dtype='<f4');digest=bytes.fromhex(calibration_sha256)
    h=HEADER.pack(b'PIV1',1,blueprint_index,frame,len(xyz),stride,0,timestamp,*matrix.ravel(),digest,len(p));body=h+p.tobytes();return body+hashlib.sha256(body).digest()
def decode(data,expected_calibration_sha256,blueprint_count):
    if len(data)<HEADER.size+32 or hashlib.sha256(data[:-32]).digest()!=data[-32:]:raise ValueError('Packet digest')
    h=HEADER.unpack(data[:HEADER.size]);magic,version,bp,frame,nraw,stride,reserved,stamp=h[:8];matrix=np.array(h[8:24]).reshape(4,4);digest=h[24];n=h[25]
    if magic!=b'PIV1' or version!=1 or not 0<=bp<blueprint_count or stride not in STRIDES or reserved!=0 or n!=(nraw+stride-1)//stride or len(data)!=HEADER.size+12*n+32 or digest.hex()!=expected_calibration_sha256:raise ValueError('Packet contract')
    raw=np.frombuffer(data,dtype='<f4',count=n*3,offset=HEADER.size).reshape(n,3)
    if not np.isfinite(raw).all() or not np.isfinite(matrix).all() or not np.isfinite(stamp) or not np.allclose(matrix[3],[0,0,0,1],rtol=0,atol=0) or not np.allclose(matrix[:3,:3].T@matrix[:3,:3],np.eye(3),rtol=0,atol=1e-6):raise ValueError('Packet geometry')
    world=raw.astype(float)@matrix[:3,:3].T+matrix[:3,3]
    return dict(frame=frame,timestamp=stamp,blueprint_index=bp,stride=stride,original_count=nraw,origin=matrix[:3,3],matrix=matrix,raw_xyz=raw,views=[dict(stride=s,points=world[::s//stride]) for s in STRIDES if s>=stride])
