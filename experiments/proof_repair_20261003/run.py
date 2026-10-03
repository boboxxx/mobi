#!/usr/bin/env python3
import argparse,hashlib,json,subprocess,time,zlib
from pathlib import Path
import numpy as np
from repair_runtime import ROOT,Proof,library
from codec import encode
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();a.out.mkdir(exist_ok=False,parents=True);(a.out/'proofs').mkdir();p=ROOT/'results/tube_evidence_20261003/replay';warm=json.loads((p/'warm.json').read_bytes());selected=[w for w in warm if (w['radius_um'],w['sigma']) in [(0,0.),(5000,.001),(50000,.01)]];assert len(selected)==36;sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};bps=sorted({s['blueprint'] for s in sources.values()});analysispath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';digest=hashlib.sha256(analysispath.read_bytes()).hexdigest();analysis=json.loads(analysispath.read_bytes());so='/tmp/mobi_repair_kernel.so';cmd=['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(HERE/'kernel.cpp'),'-o',so];subprocess.run(cmd,check=True);lib=library(so);rows=[]
 for w in selected:
  source=sources[w['old_case']];reference_name=next(c['reference'] for c in json.loads((p/'cold.json').read_bytes()) if c['proof']==w['proof']);reference=zlib.decompress((p/reference_name).read_bytes());current=zlib.decompress((p/w['current_packet']).read_bytes());archived=(p/w['message']).read_bytes();z=np.load(p/w['proof']);tree={k:z[k] for k in z.files};proof=Proof(lib,reference,digest,bps,source,(-6 if w['query_index']==0 else 6,0),analysis['summary'][w['blueprint']]['threshold'],w['radius_um'],tree);last_lower=-1;last_upper=500001
  for budget in (0,256,4096):
   timings=[];previous=None
   for rep in range(3):
    t=time.perf_counter();wire=encode(current,reference,w['radius_um'],digest,bps);enc=time.perf_counter()-t;assert wire==archived;r=proof.repaired(wire,budget);assert r['baseline_lower_us']==w['lower_us'];timings.append(dict(repeat=rep,encode_s=enc,receiver_s=r['receiver_s'],baseline_s=r['baseline_s'],repair_kernel_s=float(r['stat'][2])))
    if previous is not None:
     for k in ('cells','meta','counts','flags','witness'):np.testing.assert_array_equal(previous[k],r[k])
    previous=r
   lower,upper=map(int,r['stat'][:2]);assert lower>=last_lower and upper<=last_upper;last_lower,last_upper=lower,upper
   if budget==0:assert lower==w['lower_us'] and upper==w['upper_us']
   name='proofs/'+Path(w['message']).stem+'_b'+str(budget)+'.npz';np.savez_compressed(a.out/name,**{k:r[k] for k in ('cells','meta','counts','flags','witness')});row={k:w[k] for k in ('blueprint','query_index','radius_um','sigma','old_case','current_case','current_packet','proof','output','message','wire_bytes','packet_encode_s','source_timestamp','source_frame')};row.update(budget=budget,repair_output=name,repair_sha256=hashlib.sha256((a.out/name).read_bytes()).hexdigest(),nodes=len(r['cells']),baseline_lower_us=w['lower_us'],lower_us=lower,upper_us=upper,gap_us=upper-lower,visits=int(r['stat'][4]),new_bound_calls=int(r['stat'][5]),witness_calls=int(r['stat'][6]),has_witness=bool(r['stat'][7]),restore_s=proof.restore_s,timings=timings);rows.append(row);print(json.dumps({k:row[k] for k in ('blueprint','query_index','radius_um','budget','baseline_lower_us','lower_us','upper_us','visits','has_witness')}),flush=True)
  proof.close()
 (a.out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');deps=[HERE/f for f in ('kernel.cpp','repair_runtime.py','run.py','PROTOCOL.md')]+[ROOT/'experiments/tube_evidence_20261003'/f for f in ('kernel.cpp','runtime.py','codec.py')]+[ROOT/'experiments/expiry_runtime_20261003/kernel.cpp'];(a.out/'manifest.json').write_text(json.dumps(dict(rows=len(rows),compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],command=cmd,prior_artifact_manifest_sha256=hashlib.sha256((p.parent/'artifact_manifest.json').read_bytes()).hexdigest(),source_hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in deps}),indent=2)+'\n')
if __name__=='__main__':main()
