#!/usr/bin/env python3
"""Cold transport coding measured separately after the finite replay."""
import argparse,hashlib,json,time,zlib
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();cold=json.loads((a.results/'cold.json').read_bytes());rows=[]
 for name in sorted({r['reference'] for r in cold}):
  packet=zlib.decompress((a.results/name).read_bytes())
  for rep in range(5):
   t=time.perf_counter_ns();compressed=zlib.compress(packet);wire=compressed+hashlib.sha256(compressed).digest();u=time.perf_counter_ns();assert hashlib.sha256(wire[:-32]).digest()==wire[-32:];restored=zlib.decompress(wire[:-32]);v=time.perf_counter_ns();assert restored==packet;assert len(wire)==next(r['reference_install_bytes'] for r in cold if r['reference']==name);rows.append(dict(reference=name,repeat=rep,encode_ns=u-t,decode_ns=v-u,wire_bytes=len(wire),packet_sha256=hashlib.sha256(packet).hexdigest()))
 a.out.write_text(json.dumps(dict(rows=rows,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Five repeated cold compression/hash/decompression costs. Raw packet creation and decoded proof construction are already measured in replay. No sensor/callback or real wireless measurement.'),indent=2)+'\n')
if __name__=='__main__':main()
