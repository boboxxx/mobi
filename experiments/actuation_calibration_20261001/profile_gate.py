#!/usr/bin/env python3
"""Finite inference/containment timing; not an execution-tail guarantee."""
import argparse,csv,gzip,json,math,sys,time
from pathlib import Path
import numpy as np
from model import predict,SCALES
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lease_handoff_20261001'))
from lease import Reader,State,contains,ticks,PREFIX,pp


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--packet',type=Path,required=True);a=ap.parse_args();models=json.loads((a.results/'analysis/models.json').read_text());expected={(r['id'],r['kind']):r['counterfactual_admit']=='True' for r in csv.DictReader((a.results/'analysis/test_predictions.csv').open())};rows=[]
    blob=a.packet.read_bytes();_,n,_,_=PREFIX.unpack_from(blob);h=json.loads(blob[PREFIX.size:PREFIX.size+n]);s=h['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);reader=Reader({k:pp.Profile(**v) for k,v in h['profiles'].items()},pp.Contract(**h['contract']),s['episode'],s['frame_id']);now=h['reference_us']/pp.TIME_SCALE+.13;identity=reader.accept(blob,scope,now);assert identity;region=reader.regions[identity]
    records=[json.loads(gzip.decompress(p.read_bytes())) for p in sorted((a.results/'capture/episodes').glob('test_*.json.gz'))];assert len(records)==400
    for i,r in enumerate(records):
        for kind in (['constant','state'] if i%2==0 else ['state','constant']):
            m=models[kind];weights=None if m['weights'] is None else np.asarray(m['weights']);q=math.inf if m['q'] is None else m['q']
            def gate(time_now):
                bound=predict(r,kind,weights)+q*SCALES
                if not np.isfinite(bound).all():return False
                state=State(s['query'][0],s['query'][1],h['yaw'],r['features']['speed'])
                return ticks(time_now)+ticks(bound[3])<region.expires_us and contains(region,state,np.array([-2-bound[1],-1-bound[2]]),np.array([2+bound[0],1+bound[2]]),.03)
            start=time.perf_counter();decision=gate(now);duration=time.perf_counter()-start;assert decision==expected[(r['request']['id'],kind)]
            rows.append(dict(id=r['request']['id'],kind=kind,gate_ms=duration*1000,original=decision,including_measured_gate=gate(now+duration),plus_1ms=gate(now+duration+.001)))
    with (a.results/'gate_profile.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    out={}
    for kind in models:
        subset=[r for r in rows if r['kind']==kind];t=[r['gate_ms'] for r in subset];out[kind]=dict(cases=len(subset),median_ms=float(np.median(t)),p95_ms=float(np.quantile(t,.95)),maximum_ms=max(t),original=sum(r['original'] for r in subset),including_measured_gate=sum(r['including_measured_gate'] for r in subset),plus_1ms=sum(r['plus_1ms'] for r in subset))
    out['scope']='Loaded model and current-state features, previously verified region; no sensor acquisition, feature estimation, ray verification or actuator/network execution tail included.'
    (a.results/'gate_profile.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))


if __name__=='__main__':main()
