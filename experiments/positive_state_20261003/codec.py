"""Quantized center-union evidence with pinned contract and calibration digests."""
import hashlib,struct
import numpy as np
HEADER=struct.Struct('<4sHHIIdI32s32s')

def encode(centers_cm,radius_um,frame,timestamp,class_index,contract,calibration,refused=False):
    c=np.asarray(centers_cm,dtype='<i4').reshape(-1,2)
    if refused:c=np.empty((0,2),dtype='<i4');radius_um=0
    if not np.isfinite(timestamp) or timestamp<0 or radius_um is None or radius_um<0 or len(c)>10000:raise ValueError('Invalid evidence')
    body=HEADER.pack(b'PCS1',1,int(refused),class_index,frame,timestamp,radius_um,bytes.fromhex(contract),bytes.fromhex(calibration))+struct.pack('<I',len(c))+c.tobytes()
    return body+hashlib.sha256(body).digest()

def decode(packet,contract,calibration,class_index,radius_um):
    if len(packet)<HEADER.size+4+32 or hashlib.sha256(packet[:-32]).digest()!=packet[-32:]:raise ValueError('Integrity/length')
    h=HEADER.unpack(packet[:HEADER.size]);n=struct.unpack('<I',packet[HEADER.size:HEADER.size+4])[0]
    if h[:2]!=(b'PCS1',1) or h[2] not in (0,1) or h[3]!=class_index or not np.isfinite(h[5]) or h[5]<0 or h[7].hex()!=contract or h[8].hex()!=calibration or n>10000 or len(packet)!=HEADER.size+4+8*n+32:raise ValueError('Identity/format')
    refused=bool(h[2])
    if (refused and (n or h[6])) or (not refused and (not n or h[6]!=radius_um)):raise ValueError('Set/radius')
    c=np.frombuffer(packet,dtype='<i4',count=2*n,offset=HEADER.size+4).reshape(-1,2).copy()
    return dict(centers_cm=c,radius_um=h[6],frame=h[4],timestamp=h[5],refused=refused)
