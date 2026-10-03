#!/usr/bin/env python3
"""Independent codec/current-source identity checks and bit-change sensitivity."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=[];sens=[];p=a.results;manifest=json.loads((p/'manifest.json').read_bytes());cal=ROOT/'results/terrain_score_20261003/analysis_sheng.json';assert hashlib.sha256(cal.read_bytes()).hexdigest()==manifest['analysis_sha256'];sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};bps=sorted({s['blueprint'] for s in sources.values()});header=struct.Struct('<4sHHIIHHd16d32sI');(p/'delta_packets').mkdir(exist_ok=True)
 for wi,w in enumerate(json.loads((p/'warm.json').read_bytes())):
  old=zlib.decompress((p/w['old_packet']).read_bytes());new=zlib.decompress((p/w['current_packet']).read_bytes());assert len(old)==len(new);oh=header.unpack(old[:header.size]);nh=header.unpack(new[:header.size]);s=sources[w['current_case']];assert nh[2]==oh[2]==bps.index(w['blueprint']);assert nh[24].hex()==oh[24].hex()==manifest['analysis_sha256'];assert nh[3]==w['current_frame']==s['source_frame'] and oh[3]==w['source_frame'];assert nh[7]==w['current_timestamp']==s['source_timestamp'] and oh[7]==w['source_timestamp'];assert nh[3]>oh[3] and nh[7]>oh[7];assert nh[8:24]==oh[8:24] and nh[4:7]==oh[4:7];assert nh[25]==oh[25];assert nh[25]*12+header.size+32==len(new)
  delta=bytes(x^y for x,y in zip(old,new));wire=struct.pack('<4sI32s32s',b'PRF1',len(new),hashlib.sha256(old).digest(),hashlib.sha256(new).digest())+zlib.compress(delta);assert len(wire)==w['wire_bytes'] and hashlib.sha256(wire).hexdigest()==w['wire_sha256'];restored=bytes(x^y for x,y in zip(old,zlib.decompress(wire[72:])));assert restored==new;assert hashlib.sha256(new[:-32]).digest()==new[-32:];assert len(zlib.compress(old))+32==w['reference_install_bytes']
  fname=w['blueprint'].replace('.','_')+'_q'+str(w['query_index'])+'.bin';(p/'delta_packets'/fname).write_bytes(wire);out.append(dict(blueprint=w['blueprint'],query=w['query_index'],wire_bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest(),bit_exact=True,source_timestamp=nh[7]))
  if w['query_index']==0:
   xo=np.frombuffer(old,dtype='<f4',offset=header.size,count=oh[25]*3).reshape(-1,3);xn=np.frombuffer(new,dtype='<f4',offset=header.size,count=nh[25]*3).reshape(-1,3);rng=np.random.default_rng(20261003+wi)
   for sigma in (0.,.001,.01):
    noisy=(xn+rng.normal(0,sigma,xn.shape)).astype('<f4') if sigma else xn;mask=np.any(xo.view(np.uint32)!=noisy.view(np.uint32),axis=1);sens.append(dict(blueprint=w['blueprint'],synthetic_sigma_m=sigma,changed_rows=int(mask.sum()),rows=len(mask),scope='Bit-change diagnostic only; synthetic perturbation is not a calibrated sensor model and no expiry authorization is evaluated.'))
 a.out.write_text(json.dumps(dict(packets=out,noise_bit_sensitivity=sens,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Independent byte format reconstruction with explicit current timestamps. Wire fingerprints authenticated only for integrity, not sender identity. Fixed-scene exact-float coherence is a tested premise, not established real-LiDAR robustness.'),indent=2)+'\n')
if __name__=='__main__':main()
