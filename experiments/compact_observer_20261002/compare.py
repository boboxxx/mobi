#!/usr/bin/env python3
"""Exact finite comparison against the frozen full-domain observer outputs."""
import argparse,hashlib,json,zlib
from pathlib import Path
import numpy as np
from analyze import unpack


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    s=json.loads((a.results/'study/analysis.json').read_bytes());old=json.loads((a.baseline/'study/analysis.json').read_bytes());fine=json.loads((a.baseline/'refined/analysis.json').read_bytes());checks=0;targets=0;inputs={};rows=[];wire_pairs=[]
    for ctx in s['contexts']:
        name=ctx['run']
        for method,factor,folder in [('coarse_set',1,'study'),('fine_set',2,'refined')]:
            for identity in ['root','drive_025','drive_039']:
                new=a.results/'study/states'/(name+'_'+identity+'_'+method+'.npz');prior=a.baseline/folder/'states'/(name+'_'+identity+'.npz')
                with np.load(new) as x,np.load(prior) as y:
                    for n,domain,step in [('small',9.,.05/factor),('vehicle',11.5,.1/factor)]:
                        offset=round((15-domain)/step);nn=round(2*domain/step);crop=y[n][offset:offset+nn,offset:offset+nn]
                        assert crop.shape==x[n].shape and not (crop&~x[n]).any();checks+=1
                for p in [new,prior]:inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
                if identity=='root':continue
                source=fine['rows'] if method=='fine_set' else [r for r in old['rows'] if r['method']=='position_set' and r['repeat']==0]
                previous=next(r for r in source if r['run']==name and r['id']==identity)
                group=[r for r in s['rows'] if r['run']==name and r['id']==identity and r['method']==method]
                assert all(r['horizon_us']==previous['horizon_us'] for r in group);targets+=1
                rows.append(dict(run=name,id=identity,method=method,horizon_us=previous['horizon_us']))
    for r in s['rows']:
        if r['repeat']!=0 or not r['bytes']:continue
        stem=r['run']+'_'+r['id'];new=a.results/'study/packets'/(stem+'_'+r['method']+'.bin')
        if r['method']=='fine_set':previous=a.baseline/'refined/packets'/(stem+'.bin')
        else:previous=a.baseline/'study/packets'/(stem+('_fixed_K.bin' if r['method']=='fixed_K' else '_position_set.bin'))
        n=new.read_bytes();o=previous.read_bytes();assert o[:9]==b'MOBICV1Z\0'
        z=zlib.decompressobj();raw=z.decompress(o[9:],2100001);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(raw)<=2100000
        packet,count=unpack(n);canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        assert canonical(packet)==raw
        for p in [new,previous]:inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        wire_pairs.append(dict(run=r['run'],id=r['id'],method=r['method'],original_bytes=len(o),dictionary_bytes=len(n),templates=count))
    result=dict(class_mask_conservative_crop_checks=checks,target_horizon_equivalence_checks=targets,exact_original_packet_checks=len(wire_pairs),rows=rows,wire_pairs=wire_pairs,input_sha256=inputs,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='All saved root/final states: local possible masks contain full-domain cropped masks and all24 positional horizons match. All30 dictionaries reconstruct original typed packet bytes exactly. Finite comparison, not universal window equivalence or new timing claim.')
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ['class_mask_conservative_crop_checks','target_horizon_equivalence_checks','exact_original_packet_checks']}))


if __name__=='__main__':main()
