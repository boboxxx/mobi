#!/usr/bin/env python3
"""Reuse the frozen runner with a different conservative bound implementation."""
import hashlib,json,sys
from pathlib import Path
import run
from refined import RefinedIndex
def main():
    here=Path(__file__).resolve().parent;root=here.parents[1];manifest=here/'refinement_manifest.json'
    for p,h in json.loads(manifest.read_bytes()).items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
    run.RayIndex=RefinedIndex
    run.main()
    out=Path(sys.argv[sys.argv.index('--out')+1]);file=out/'manifest.json';m=json.loads(file.read_bytes());m['bound_variant']='componentwise_rotation_and_count_complement';m['refinement_protocol_sha256']=hashlib.sha256((here/'PROTOCOL_REFINED.md').read_bytes()).hexdigest();m['refinement_manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest();file.write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':main()
