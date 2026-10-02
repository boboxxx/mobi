#!/usr/bin/env python3
"""Finite saved-input diagnostic; no receiver cost or timing claim."""
import argparse, hashlib, json
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[2];study=json.loads((a.source/'study/analysis.json').read_bytes());rows=[];inputs={}
    for ctx in study['contexts']:
        signatures=[]
        for index in range(20,40):
            path=a.source/'study/source'/(ctx['run']+'_drive_%03d.json'%index);p=json.loads(path.read_bytes())['payload'];inputs[str(path)]=sha(path)
            # Exact quantized geometry and relative ages; no float rounding or
            # unbounded similarity cache. This alone is NOT a valid cache key:
            # scope, physical/error/motion contracts and grid also matter.
            rays=[r[:4]+[p['reference_us']-r[4]] for r in p['rays']]
            signatures.append(hashlib.sha256(json.dumps([p['origins'],rays],sort_keys=True,separators=(',',':')).encode()).hexdigest())
        rows.append(dict(run=ctx['run'],source_steps=20,unique_geometry_age_signatures=len(set(signatures)),signatures=signatures))
    result=dict(rows=rows,input_sha256=inputs,source_study_sha256=sha(a.source/'study/analysis.json'),
                diagnostic_sha256=sha(Path(__file__)),scope='All120 saved source records only; exact origins/endpoints/relative ray ages. Does not test moving geometry, justify unchecked cache, or measure new costs.')
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({x['run']:x['unique_geometry_age_signatures'] for x in rows}))


if __name__=='__main__':main()
