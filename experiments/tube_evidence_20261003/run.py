#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,subprocess,time,zlib
from pathlib import Path
import numpy as np
from runtime import ROOT,Proof,library
from codec import encode as encode_tube
from packet import encode as encode_full
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('terrain_point_score',ROOT/'experiments/terrain_score_20261003/model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
def current_packet(source,digest,bps,sigma):
    with np.load(ROOT/source['source_cloud']) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']];matrix=z['transform']
    seed=int(hashlib.sha256((source['case']+':tube-noise').encode()).hexdigest()[:16],16)
    if sigma:xyz=(xyz+np.random.default_rng(seed).normal(0,sigma,xyz.shape)).astype('<f4')
    times=[]
    for _ in range(5):
        start=time.perf_counter();packet=encode_full(np.column_stack((xyz[:,0],xyz[:,1],xyz[:,2])),source['source_frame'],source['source_timestamp'],matrix,4,bps.index(source['blueprint']),digest);times.append(time.perf_counter()-start)
    seconds=max(times)
    return packet,seconds,seed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--budget',type=int,default=64000);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'proofs').mkdir();(a.out/'packets').mkdir();(a.out/'messages').mkdir();sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());bps=sorted({s['blueprint'] for s in sources});analysis_path=ROOT/'results/terrain_score_20261003/analysis_sheng.json';digest=hashlib.sha256(analysis_path.read_bytes()).hexdigest();analysis=json.loads(analysis_path.read_bytes());libpath=Path('/tmp/mobi_tube_kernel.so');command=['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(HERE/'kernel.cpp'),'-o',str(libpath)];t=time.perf_counter();subprocess.run(command,check=True);compilation=dict(seconds=time.perf_counter()-t,command=command,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]);lib=library(libpath);cold=[];warm=[];inputs=[]
    for bp in bps:
        pair=sorted([s for s in sources if s['blueprint']==bp],key=lambda s:s['episode_index']);old=pair[0];current=pair[1];ref,refencode,_=current_packet(old,digest,bps,0);refname='packets/'+old['case']+'.bin.zlib';(a.out/refname).write_bytes(zlib.compress(ref));packets={}
        boot=[]
        for eps in (0,5000,50000):
            for qi,x in enumerate((-6,6)):
                proof=Proof(lib,ref,digest,bps,old,(x,0),analysis['summary'][bp]['threshold'],a.budget,eps);tag=bp.replace('.','_')+'_e'+str(eps)+'_q'+str(qi);fname='proofs/'+tag+'.npz';np.savez_compressed(a.out/fname,**proof.export());cold.append(dict(blueprint=bp,query_index=qi,radius_um=eps,budget=a.budget,reference=refname,reference_encode_s=refencode,reference_install_bytes=len(zlib.compress(ref))+32,proof=fname,proof_sha256=hashlib.sha256((a.out/fname).read_bytes()).hexdigest(),nodes=proof.n,lower_us=int(proof.stat[0]),upper_us=int(proof.stat[1]),excluded=int(proof.stat[3]),total_s=proof.total_s));print('cold '+json.dumps(cold[-1]),flush=True)
                boot.append((eps,qi,proof,tag,fname))
        for sigma in (0.,.001,.01):
            packet,enc,seed=current_packet(current,digest,bps,sigma);name='packets/'+current['case']+'_s'+str(sigma)+'.bin.zlib';(a.out/name).write_bytes(zlib.compress(packet));packets[sigma]=(packet,enc,name);inputs.append(dict(case=current['case'],blueprint=bp,sigma=sigma,seed=seed,packet=name,packet_sha256=hashlib.sha256(packet).hexdigest(),packet_encode_s=enc,reference=refname,reference_sha256=hashlib.sha256(ref).hexdigest()))
        for eps,qi,proof,tag,fname in boot:
            for sigma,(packet,pack_s,packetname) in packets.items():
                timings=[];last=None;wire=None
                for rep in range(3):
                    t=time.perf_counter();wire=encode_tube(packet,ref,eps,digest,bps);encode_s=time.perf_counter()-t;inc=proof.check(wire,True);full=proof.check(wire,False);np.testing.assert_array_equal(inc['counts'],full['counts']);np.testing.assert_array_equal(inc['accepted'],full['accepted']);np.testing.assert_array_equal(inc['stat'][[0,1,3,4]],full['stat'][[0,1,3,4]]);timings.append(dict(repeat=rep,encode_s=encode_s,incremental_s=inc['total_s'],full_recheck_s=full['total_s'],incremental_kernel_s=float(inc['stat'][2]),full_recheck_kernel_s=float(full['stat'][2])));last=inc
                message='messages/'+tag+'_s'+str(sigma)+'.bin';(a.out/message).write_bytes(wire);output='proofs/'+tag+'_s'+str(sigma)+'_warm.npz';np.savez_compressed(a.out/output,counts=last['counts'],accepted=last['accepted']);row=dict(blueprint=bp,query_index=qi,radius_um=eps,sigma=sigma,old_case=old['case'],current_case=current['case'],current_packet=packetname,packet_encode_s=pack_s,proof=fname,output=output,output_sha256=hashlib.sha256((a.out/output).read_bytes()).hexdigest(),message=message,message_sha256=hashlib.sha256(wire).hexdigest(),wire_bytes=len(wire),exceptions=last['exceptions'],input_rays=len(proof.world),lower_us=int(last['stat'][0]),upper_us=int(last['stat'][1]),excluded=int(last['stat'][3]),revoked=int(last['stat'][4]),source_timestamp=current['source_timestamp'],source_frame=current['source_frame'],timings=timings);warm.append(row);print('warm '+json.dumps({k:row[k] for k in ('blueprint','query_index','radius_um','sigma','lower_us','wire_bytes','exceptions','revoked')}),flush=True)
            proof.close()
    for name,data in [('cold.json',cold),('warm.json',warm),('inputs.json',inputs)]: (a.out/name).write_text(json.dumps(data,indent=2)+'\n')
    sourcefiles=[HERE/f for f in ['kernel.cpp','runtime.py','codec.py','run.py','PROTOCOL.md']]+[ROOT/'experiments/expiry_runtime_20261003/kernel.cpp',ROOT/'experiments/expiry_runtime_20261003/runtime.py',ROOT/'experiments/pose_inversion_20261003/packet.py',ROOT/'experiments/terrain_score_20261003/model.py'];(a.out/'manifest.json').write_text(json.dumps(dict(compilation=compilation,budget=a.budget,cold_calls=len(cold),warm_cases=len(warm),analysis_sha256=digest,source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcefiles},scope='Fixed synthetic endpoint-uncertainty study over saved sources. No new calibrated sensor distribution, physical motion or real-link claim.'),indent=2)+'\n')
if __name__=='__main__':main()
