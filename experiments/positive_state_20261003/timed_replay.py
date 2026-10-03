#!/usr/bin/env python3
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
from model import centers,quantized_centers
from codec import encode,decode
from evaluate import geometry,ROOT,HERE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=json.loads((p/'analysis_sheng.json').read_bytes());records={r['id']:r for r in json.loads((p/'capture/record.json').read_bytes()) if r['status']=='captured'};catalog=d['contract_body']['catalog'];bps=list(catalog);anchor=np.array(d['contract_body']['basis']['anchor']);road=np.array(d['contract_body']['basis']['road']);out=[]
    for r in d['rows']:
        source=records[r['id']]
        with np.load(p/'capture'/source['cloud_file']) as z:raw=z['raw'].copy();matrix=z['transform'].copy()
        ext=catalog[r['blueprint']];samples=[]
        for repeat in range(3):
            start=time.perf_counter();xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float);assembled=time.perf_counter();world=xyz@matrix[:3,:3].T+matrix[:3,3];c,meta=centers(world,anchor,road,ext);cm=quantized_centers(c);wire=encode(cm,r['radius_um'],source['frame'],source['timestamp'],bps.index(r['blueprint']),d['contract_sha256'],d['calibration_sha256'],not r['available']);decoded=decode(wire,d['contract_sha256'],d['calibration_sha256'],bps.index(r['blueprint']),r['radius_um']);bounds=geometry(decoded['centers_cm'],decoded['radius_um'],ext,decoded['refused']);end=time.perf_counter();samples.append(dict(repeat=repeat,assembly_s=assembled-start,whole_s=end-start));assert hashlib.sha256(wire).hexdigest()==r['packet_sha256'] and bounds==r['bounds']
        charged=max(max(t['whole_s'] for t in samples),max(t['pipeline_s'] for t in r['timings'])+max(t['assembly_s'] for t in samples));cost=math.ceil(240000+source['acquisition_s']*1e6+charged*1e6+len(wire)*.4);remaining=[max(0,b['lower_us']-cost) for b in bounds];assert all(x<=y for x,y in zip(remaining,r['modeled_remaining_us']));out.append(dict(id=r['id'],packet_sha256=r['packet_sha256'],samples=samples,charged_pipeline_s=charged,cost_us=cost,modeled_remaining_us=remaining));print('timed',r['id'],remaining,flush=True)
    deps=[HERE/n for n in ('timed_replay.py','TIMING_AUDIT.md','model.py','codec.py','evaluate.py')];a.out.write_text(json.dumps(dict(rows=out,analysis_sha256=sha(p/'analysis_sheng.json'),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in deps},scope='Processing-only timing repair. All packets and horizons unchanged. Includes previously omitted raw XYZ assembly; conservative max/sum of observed components, not WCET. Two-view episode availability remains an offline premise.'),indent=2)+'\n')
if __name__=='__main__':main()
