#!/usr/bin/env python3
"""Post-analysis exact saved-packet/mask comparison; no new timed trial."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=a.results
    s=json.loads((r/'study/analysis.json').read_bytes());f=json.loads((r/'refined/analysis.json').read_bytes());rows=[];inputs={}
    for x in f['rows']:
        name=x['run']+'_'+x['id'];p=r/'study/packets'/(name+'_position_set.bin');q=r/'refined/packets'/(name+'.bin')
        assert p.read_bytes()==q.read_bytes()
        coarse=r/'study/states'/(name+'.npz');fine=r/'refined/states'/(name+'.npz');changes={}
        with np.load(coarse) as c,np.load(fine) as d:
            assert set(c.files)==set(d.files)
            for n in c.files:
                lifted=np.repeat(np.repeat(c[n],2,axis=0),2,axis=1)
                assert d[n].shape==lifted.shape and not (d[n]&~lifted).any()
                changes[n]=dict(lifted_possible_tiles=int(lifted.sum()),fine_possible_tiles=int(d[n].sum()))
        old=next(y for y in s['rows'] if y['run']==x['run'] and y['id']==x['id'] and y['method']=='position_set' and y['repeat']==0)
        assert x['horizon_us']>=old['horizon_us']
        for t in [p,q,coarse,fine]:inputs[str(t.relative_to(r))]=hashlib.sha256(t.read_bytes()).hexdigest()
        rows.append(dict(run=x['run'],id=x['id'],coarse_horizon_us=old['horizon_us'],fine_horizon_us=x['horizon_us'],classes=changes))
    result=dict(packet_pairs=len(rows),class_mask_containment_checks=2*len(rows),rows=rows,input_sha256=inputs,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='ALL12 archived fine/coarse observations have byte-identical transport; fine possible sets are subsets of lifted coarse sets. Post-analysis exact comparison, no timing or generalization claim.')
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ['packet_pairs','class_mask_containment_checks']}))


if __name__=='__main__':main()
