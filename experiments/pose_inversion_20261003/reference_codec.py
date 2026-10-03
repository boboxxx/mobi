#!/usr/bin/env python3
"""Lossless shared-design-scan codec; reference is compression state, never evidence."""
import argparse,hashlib,json,math,struct,time,zlib
from pathlib import Path
import numpy as np
from packet import HEADER
ROOT=Path(__file__).resolve().parents[2]
REF='results/physical_contract_20261002/capture/clouds/vehicle_audi_a2_y000_v0.npz'
WIRE=struct.Struct('<4sI32s32s')
def encode(payload,reference):
    if len(payload)!=len(reference):raise ValueError('Reference length')
    diff=np.frombuffer(payload,dtype='u1')^np.frombuffer(reference,dtype='u1')
    return WIRE.pack(b'PRF1',len(payload),hashlib.sha256(reference).digest(),hashlib.sha256(payload).digest())+zlib.compress(diff.tobytes())
def decode(wire,reference):
    if reference is None:raise ValueError('Missing reference')
    if len(wire)<WIRE.size:raise ValueError('Truncated wire')
    magic,n,rh,ph=WIRE.unpack(wire[:WIRE.size])
    if magic!=b'PRF1' or n!=len(reference) or hashlib.sha256(reference).digest()!=rh:raise ValueError('Reference mismatch')
    diff=zlib.decompress(wire[WIRE.size:])
    if len(diff)!=n:raise ValueError('Payload length')
    raw=(np.frombuffer(diff,dtype='u1')^np.frombuffer(reference,dtype='u1')).tobytes()
    if hashlib.sha256(raw).digest()!=ph:raise ValueError('Payload mismatch')
    return raw

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--timings',type=Path,required=True);a=ap.parse_args()
    with np.load(ROOT/REF) as z:xyz=np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']].astype('<f4')
    refs={s:bytes(HEADER.size)+xyz[::s].tobytes()+bytes(32) for s in (16,4,1)}
    full=refs[1];setup=zlib.compress(full);assert zlib.decompress(setup)==full
    # Receiver gets this reference explicitly, verifies its hash, then derives all nested references.
    setup_bytes=len(setup)+32
    entries=[];times=[];seen=set()
    for row in json.loads((a.results/'replay/rows.json').read_bytes()):
        key=(row['case'],row['stride'])
        if key in seen:continue
        seen.add(key);raw=zlib.decompress((a.results/'replay'/row['packet_file']).read_bytes());ref=refs[key[1]]
        for repeat in range(3):
            t=time.perf_counter_ns();wire=encode(raw,ref);u=time.perf_counter_ns();restored=decode(wire,ref);v=time.perf_counter_ns();assert restored==raw
            times.append(dict(case=key[0],stride=key[1],repeat=repeat,encode_ns=u-t,decode_ns=v-u))
        for bad in [None,bytes(len(ref)),ref[:-1]]:
            try:decode(wire,bad)
            except ValueError:pass
            else:raise AssertionError('Reference failure did not refuse')
        corrupted=bytearray(wire);corrupted[40]^=1
        try:decode(bytes(corrupted),ref)
        except ValueError:pass
        else:raise AssertionError('Digest failure did not refuse')
        entries.append(dict(case=key[0],stride=key[1],wire_bytes=len(wire),raw_sha256=hashlib.sha256(raw).hexdigest(),wire_sha256=hashlib.sha256(wire).hexdigest(),reference_sha256=hashlib.sha256(ref).hexdigest(),warm_zero_compute_fixed_cost_us=math.ceil(len(wire)*.4+240000),cold_zero_compute_fixed_cost_us=math.ceil((len(wire)+setup_bytes)*.4+240000)))
    a.out.write_text(json.dumps(dict(reference=REF,reference_file_sha256=hashlib.sha256((ROOT/REF).read_bytes()).hexdigest(),setup_wire_bytes=setup_bytes,setup_raw_bytes=len(full),packets=entries,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Retrospective fixed-scene lossless baseline. Complete bitwise reconstruction of current packet, including current source time. Cold cost pays reference setup; warm cost assumes verified cache already installed. Reference never supplies unobserved current rays or free-space evidence. Link remains modeled; CPU timings separate.'),indent=2)+'\n')
    a.timings.write_text(json.dumps(times,indent=2)+'\n');print(json.dumps(dict(packets=len(entries),setup_bytes=setup_bytes,full_wire_bytes=[r['wire_bytes'] for r in entries if r['stride']==1])))
if __name__=='__main__':main()
