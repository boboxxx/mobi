#!/usr/bin/env python3
"""Measure otherwise omitted current-packet creation and cold-reference encoding."""
import argparse,hashlib,json,time,zlib
from pathlib import Path
import numpy as np
from runtime import ROOT,encode

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());bps=sorted({s['blueprint'] for s in sources});digest=hashlib.sha256((ROOT/'results/terrain_score_20261003/analysis_sheng.json').read_bytes()).hexdigest();rows=[]
 for s in sources:
  with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];matrix=z['transform']
  for repeat in range(5):
   t=time.perf_counter_ns();packet=encode(np.c_[raw['x'],raw['y'],raw['z']],s['source_frame'],s['source_timestamp'],matrix,4,bps.index(s['blueprint']),digest);u=time.perf_counter_ns();reference=zlib.compress(packet);v=time.perf_counter_ns();restored=zlib.decompress(reference);w=time.perf_counter_ns();assert restored==packet;rows.append(dict(case=s['case'],repeat=repeat,packet_encode_ns=u-t,cold_reference_encode_ns=v-u,cold_reference_decode_ns=w-v,raw_bytes=len(packet),cold_reference_bytes=len(reference)+32,packet_sha256=hashlib.sha256(packet).hexdigest()))
 a.out.write_text(json.dumps(dict(rows=rows,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Sensor-data arrays already received in process; includes xyz packing, packet metadata/hash, and lossless cold-reference coding. Data capture and physical sensing latency remain unmeasured.'),indent=2)+'\n')
if __name__=='__main__':main()
