"""Supplemental malformed-packet checks, preserving the original freeze."""
import hashlib
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/action_window_reference_20261011'))
import kernel as k

def packet(fields,payload):
    body=k.HEADER.pack(*fields)+payload
    return body+hashlib.sha256(body).digest()

def main():
    fields=[b'AWI1',1_000_000,50_000,2,1,20,6,2,k.context_digest(0)]
    cases=[]
    for spans in (((0,2),(2,4)),((0,2),(3,4)),((2,1),(4,4)),((0,2),(4,7))):
        cases.append(packet(fields,b''.join(struct.pack('!HH',*s) for s in spans)))
    for index,value in ((0,b'BAD!'),(1,-1),(2,0),(3,0),(4,21),(5,0),(7,9)):
        f=list(fields);f[index]=value
        cases.append(packet(f,struct.pack('!HHHH',0,2,4,6)))
    f=list(fields);f[0]=b'AWB1';f[7]=7
    cases.append(packet(f,bytes([128])))
    f[7]=6;cases.append(packet(f,bytes([0])))
    for raw in cases:
        try:k.decode(raw)
        except ValueError:continue
        raise AssertionError('malformed contract accepted')
    print('SUPPLEMENTAL_CODEC_CONTRACT_CHECKS_PASS',len(cases))

if __name__=='__main__':main()
