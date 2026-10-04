#!/usr/bin/env python3
"""Lossless publication representation for the >100 MiB analysis file."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/prospective_shape_20261004'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pack',action='store_true');a=ap.parse_args();src=P/'analysis_sheng.json';gz=P/'analysis_sheng.json.gz';receipt=P/'archive_representation.json'
 if a.pack:
  assert not receipt.exists();data=src.read_bytes()
  with gz.open('wb') as f:
   with gzip.GzipFile(filename='',mode='wb',fileobj=f,compresslevel=6,mtime=0) as z:z.write(data)
  receipt.write_text(json.dumps(dict(materialized_file=src.name,materialized_sha256=sha(data),materialized_bytes=len(data),archived_file=gz.name,archived_sha256=sha(gz.read_bytes()),archived_bytes=gz.stat().st_size,scope='Lossless gzip representation to satisfy GitHub single-file limit; no analysis/data change.'),indent=2)+'\n')
 r=json.loads(receipt.read_bytes());b=gz.read_bytes();assert sha(b)==r['archived_sha256'];data=gzip.decompress(b);assert len(data)==r['materialized_bytes'] and sha(data)==r['materialized_sha256']
 if src.exists():assert src.read_bytes()==data
 else:src.write_bytes(data)
 print('LOSSLESS_ANALYSIS_ARCHIVE_VERIFIED',r['materialized_bytes'],r['archived_bytes'])
if __name__=='__main__':main()
