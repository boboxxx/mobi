#!/usr/bin/env python3
"""Strong lossless byte baseline and audit-only support composition diagnosis."""
import argparse,hashlib,json,math,struct,time,zlib
from pathlib import Path
import numpy as np
from audit import ROOT,rotation,face_events

def shuffled_encode(payload):
    if len(payload)%4:raise ValueError('Word alignment')
    words=np.frombuffer(payload,dtype='<u4');d=np.empty_like(words);d[:1]=words[:1];d[1:]=words[1:]^words[:-1];shuffled=np.ascontiguousarray(d.view('u1').reshape(-1,4).T).tobytes();return struct.pack('<4sI',b'BXZ1',len(payload))+zlib.compress(shuffled)
def shuffled_decode(data):
    magic,n=struct.unpack('<4sI',data[:8]);assert magic==b'BXZ1' and n%4==0;raw=zlib.decompress(data[8:]);assert len(raw)==n;words=np.ascontiguousarray(np.frombuffer(raw,dtype='u1').reshape(4,-1).T).view('<u4').ravel();return np.bitwise_xor.accumulate(words).astype('<u4',copy=False).tobytes()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--timings',type=Path,required=True);a=ap.parse_args();p=a.results;rows=json.loads((p/'replay/rows.json').read_bytes());sources={s['case']:s for s in json.loads((p/'replay/sources.json').read_bytes())};bank=json.loads((p/'witness_bank_sheng.json').read_bytes());packets=[];timings=[];seen=set()
    for row in rows:
        key=(row['case'],row['stride'])
        if key in seen:continue
        seen.add(key);payload=zlib.decompress((p/'replay'/row['packet_file']).read_bytes())
        for name,encoder,decoder in [('raw',lambda b:b,lambda b:b),('zlib',zlib.compress,zlib.decompress),('xor_byte_shuffle_zlib',shuffled_encode,shuffled_decode)]:
            for repeat in range(3):
                t=time.perf_counter_ns();wire=encoder(payload);u=time.perf_counter_ns();restored=decoder(wire);v=time.perf_counter_ns();assert restored==payload;timings.append(dict(case=key[0],stride=key[1],codec=name,repeat=repeat,encode_ns=u-t,decode_ns=v-u))
            packets.append(dict(case=key[0],stride=key[1],codec=name,wire_bytes=len(wire),raw_sha256=hashlib.sha256(payload).hexdigest(),wire_sha256=hashlib.sha256(wire).hexdigest(),zero_compute_fixed_cost_us=math.ceil(len(wire)*8/20000000*1e6+240000)))
    support=[]
    for case,s in sources.items():
        rr=json.loads((ROOT/s['source_record']).read_bytes());truth=next(r for r in rr if r.get('id')==s['source_id'])
        with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];world=np.c_[raw['x'],raw['y'],raw['z']].astype(float)@z['transform'][:3,:3].T+z['origin'];origin=z['origin']
        for candidate in bank['candidates']:
            if candidate['case']!=case or not candidate['accepted_by_stride']['1']:continue
            pose=np.array(candidate['pose']);center=np.array(s['anchor'])+np.array(s['road_rotation'])@pose[:3];eligible,leave=face_events(world,origin,center,rotation(pose[3:]),np.array(s['extent'])+.03);nonpassing=eligible&(leave>=1-1e-10);n=int(nonpassing.sum());ground=int(np.sum(nonpassing&(abs(world[:,2]-s['anchor'][2])<=.05)));own=int(np.sum(nonpassing&(raw['id']==truth['actor_id'])));support.append(dict(case=case,query_index=candidate['query_index'],pose=candidate['pose'],upper_us=candidate['upper_us'],nonpassing_returns=n,near_road_height_returns=ground,actual_actor_returns=own,near_road_fraction=ground/n if n else None,all_nonpassing_near_road=bool(n and ground==n),no_actual_actor_support=own==0))
    out=dict(packets=packets,support=support,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),witness_bank_sha256=hashlib.sha256((p/'witness_bank_sheng.json').read_bytes()).hexdigest(),scope='Additional retrospective diagnostics. Lossless codecs preserve the exact original payload and posterior; measured codec costs are separate. Near-road height and actor IDs are audit-only, not a new online ground classifier or validated modified score.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');a.timings.write_text(json.dumps(timings,indent=2)+'\n');print(json.dumps(dict(packet_codec_pairs=len(packets),full_surviving_candidates=len(support),ground_only_nonpassing=sum(x['all_nonpassing_near_road'] for x in support),no_actual_actor_support=sum(x['no_actual_actor_support'] for x in support))))
if __name__=='__main__':main()
