#!/usr/bin/env python3
import argparse,gzip,hashlib,json,time,zlib
from pathlib import Path
import numpy as np
from runtime import ROOT,HERE,library,compile_kernel,make_packet,Proof,encode_delta,decode_delta

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--budget',default=16000,type=int);ap.add_argument('--library',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'proofs').mkdir();(a.out/'packets').mkdir();libpath=a.library or Path('/tmp/mobi_expiry_runtime.so');compilation=None if a.library else compile_kernel(libpath);lib=library(libpath);sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());analysispath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';analysis=json.loads(analysispath.read_bytes());digest=hashlib.sha256(analysispath.read_bytes()).hexdigest();bps=sorted({s['blueprint'] for s in sources});rows=[];warm=[]
    for bp in bps:
        pair=sorted([s for s in sources if s['blueprint']==bp],key=lambda s:s['episode_index']);assert [s['episode_index'] for s in pair]==[0,10];packets=[make_packet(s,digest,bps) for s in pair];packetnames=[]
        for s,packet in zip(pair,packets):
            name='packets/'+s['case']+'.bin.zlib';(a.out/name).write_bytes(zlib.compress(packet));packetnames.append(name)
        setup=len(zlib.compress(packets[0]))+32
        for qi,x in enumerate((-6,6)):
            old=None
            for position,(s,packet) in enumerate(zip(pair,packets)):
                proof=Proof(lib,packet,digest,bps,s['extent'],s['anchor'],s['road_rotation'],(x,0),analysis['summary'][bp]['threshold'],a.budget);name='proofs/'+s['case']+'_q'+str(qi)+'.npz';np.savez_compressed(a.out/name,**proof.export());rows.append(dict(case=s['case'],blueprint=bp,query_index=qi,budget=a.budget,packet=packetnames[position],packet_sha256=hashlib.sha256(packet).hexdigest(),proof=name,proof_sha256=hashlib.sha256((a.out/name).read_bytes()).hexdigest(),lower_us=int(proof.stat[0]),upper_us=int(proof.stat[1]),kernel_s=float(proof.stat[2]),total_s=proof.total_s,excluded=int(proof.stat[3]),inspected=int(proof.stat[4]),nodes=proof.n));print(json.dumps(rows[-1]),flush=True)
                if position==0:old=proof
                else:
                    timings=[];last=None
                    for repeat in range(3):
                        t=time.perf_counter();wire=encode_delta(packet,packets[0]);encode_s=time.perf_counter()-t;t=time.perf_counter();rebuilt=decode_delta(wire,packets[0]);decode_s=time.perf_counter()-t;assert rebuilt==packet
                        inc=old.check(rebuilt,True);full=old.check(rebuilt,False);np.testing.assert_array_equal(inc['counts'],full['counts']);np.testing.assert_array_equal(inc['accepted'],full['accepted']);np.testing.assert_array_equal(inc['stat'][[0,1,3,4]],full['stat'][[0,1,3,4]]);timings.append(dict(repeat=repeat,encode_s=encode_s,decode_s=decode_s,incremental_s=inc['total_s'],full_recheck_s=full['total_s'],incremental_kernel_s=float(inc['stat'][2]),full_recheck_kernel_s=float(full['stat'][2])));last=inc
                    output='proofs/'+bp.replace('.','_')+'_q'+str(qi)+'_warm.npz';np.savez_compressed(a.out/output,counts=last['counts'],accepted=last['accepted']);warm.append(dict(blueprint=bp,query_index=qi,budget=a.budget,old_case=pair[0]['case'],current_case=s['case'],old_packet=packetnames[0],current_packet=packetnames[1],reference_install_bytes=setup,wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest(),source_frame=int(old.old['frame']),current_frame=s['source_frame'],source_timestamp=old.old['timestamp'],current_timestamp=s['source_timestamp'],changed_rays=last['changed_rays'],input_rays=last['input_rays'],lower_us=int(last['stat'][0]),upper_us=int(last['stat'][1]),remaining_excluded=int(last['stat'][3]),revoked=int(last['stat'][4]),output=output,output_sha256=hashlib.sha256((a.out/output).read_bytes()).hexdigest(),timings=timings));print('warm '+json.dumps({k:warm[-1][k] for k in ('blueprint','query_index','lower_us','wire_bytes','changed_rays','revoked')}),flush=True);old.close();proof.close()
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');(a.out/'warm.json').write_text(json.dumps(warm,indent=2)+'\n');(a.out/'manifest.json').write_text(json.dumps(dict(compilation=compilation,budget=a.budget,calls=len(rows),warm_calls=len(warm),analysis_sha256=digest,source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'kernel.cpp',HERE/'runtime.py',HERE/'run.py',HERE/'PROTOCOL.md',ROOT/'experiments/pose_inversion_20261003/packet.py',ROOT/'experiments/pose_inversion_20261003/reference_codec.py']},scope='Finite retrospective native and fresh-current-packet delta revalidation. Same score, priors, uncertain dynamics. Full recheck on identical inherited partition is the paired baseline. Current source times retained; wire modeled.'),indent=2)+'\n')
if __name__=='__main__':main()
