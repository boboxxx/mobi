#!/usr/bin/env python3
"""Exploratory direct task-expiry calibration on fixed saved current messages."""
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
import evaluate as primary
from tube import geometry
from engine import replay
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def grid_deadlines(r,ep,ext):
    body=math.ceil(float(np.linalg.norm(ext))*1e6)/1e6;road=np.array(r['road']);anchor=np.array(r['anchor']);out=[]
    for qx in (-6.,6.):
        g=500000
        for state in ep['trajectory'][r['step']:r['step']+11]:
            true=(np.array(state['center'])-anchor)@road
            if float(np.linalg.norm(true[:2]-[qx,0.]))<=body+.75:
                g=max(-1,math.floor(state['timestamp']*1e6)-r['source_us']-1);break
        out.append(g)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'analysis_sheng.json').read_bytes());byep={e['episode']['id']:e for e in d['episodes']};catalog=d['contract_body']['catalog'];bps=list(catalog);scores={k:0 for k in byep};base={};truth={}
    for r in d['rows']:
        cm=np.array(r['centers_cm'],dtype=np.int32).reshape(-1,2);base[r['id']]=geometry(cm,8000,catalog[r['blueprint']],not r['available']);truth[r['id']]=grid_deadlines(r,byep[r['episode_id']],catalog[r['blueprint']])
        if r['available']:scores[r['episode_id']]=max(scores[r['episode_id']],max(max(0,b['lower_us']-g) for b,g in zip(base[r['id']],truth[r['id']])))
    registry={bp:dict(correction_us=max(scores[e['episode']['id']] for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'),calibration_n=95,rank=95) for bp in bps}
    policy_body=dict(primary_contract_sha256=d['contract_sha256'],primary_calibration_sha256=d['calibration_sha256'],protocol_sha256=sha(HERE/'FUNCTIONAL_PROTOCOL.md'),registry=registry);policy=hashlib.sha256(json.dumps(policy_body,sort_keys=True).encode()).hexdigest();out=[]
    for r in d['rows']:
        bp=r['blueprint'];ext=catalog[bp];ci=bps.index(bp);delta=registry[bp]['correction_us'];cm=np.array(r['centers_cm'],dtype=np.int32).reshape(-1,2);bounds=[dict(lower_us=max(-1,b['lower_us']-delta),upper_us=max(-1,b['upper_us']-delta)) for b in base[r['id']]];methods={}
        for method in ('union','lossless_centers','full_xyz'):
            old=r['methods'][method];wire=(p/old['packet']).read_bytes();samples=[]
            for repeat in range(3):
                start=time.perf_counter()
                assert hashlib.sha256(json.dumps(policy_body,sort_keys=True).encode()).hexdigest()==policy
                if method=='union':decoded=primary.decode(wire,d['contract_sha256'],d['calibration_sha256'],ci,r['radius_um']);current=decoded['centers_cm'];refused=decoded['refused']
                else:current=primary.unpack_other(wire,b'RXYZ' if method=='full_xyz' else b'LCEN',ci,d['contract_sha256'],d['calibration_sha256'],np.array(r['anchor']),np.array(r['road']),ext);refused=not len(current)
                got=[dict(lower_us=max(-1,b['lower_us']-delta),upper_us=max(-1,b['upper_us']-delta)) for b in geometry(current,8000,ext,refused)];end=time.perf_counter();assert got==bounds
                samples.append(dict(source_s=old['samples'][repeat]['source_s'],selection_s=old['samples'][repeat]['selection_s'],receiver_s=end-start))
            methods[method]=dict(wire_bytes=old['wire_bytes'],wire_sha256=old['wire_sha256'],packet=old['packet'],samples=samples,source_us=old['source_us'],receiver_us=math.ceil(max(s['receiver_s'] for s in samples)*1e6))
        methods['fixed200']=dict(methods['union']);g=truth[r['id']];violation=r['available'] and any(b['lower_us']>x for b,x in zip(bounds,g));out.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,split=r['split'],step=r['step'],layout=r['layout'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],available=r['available'],base_bounds=base[r['id']],bounds=bounds,grid_oracle_us=g,deadline_overstatement=bool(violation),methods=methods))
        if len(out)%200==0:print('functional',len(out),flush=True)
    traces=[];summary=[]
    for bp in bps:
        ee=[e for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in out if r['blueprint']==bp and r['split']=='test'];summary.append(dict(blueprint=bp,**registry[bp],test_episodes=60,deadline_overstatement_episodes=sum(any(r['deadline_overstatement'] for r in rr if r['episode_id']==e['episode']['id']) for e in ee)))
        for ep in ee:
            fr=[r for r in rr if r['episode_id']==ep['episode']['id']];t0=fr[0]['source_us'] if fr else 0;oracle=[dict(r,bounds=[dict(lower_us=g) for g in r['grid_oracle_us']]) for r in fr]
            for rate in (20000000,2000000):
                for method in ('union','lossless_centers','full_xyz','fixed200'):traces.append(dict(episode_id=ep['episode']['id'],blueprint=bp,bitrate=rate,method=method,**replay(fr,method,rate,t0),oracle_grants=replay(oracle,method,rate,t0)['grants']))
    files=[HERE/n for n in ('functional.py','FUNCTIONAL_PROTOCOL.md','FUNCTIONAL_THEORY.md','engine.py','evaluate.py','tube.py')];result=dict(registry=registry,episode_scores=scores,rows=out,traces=traces,summary=summary,policy_body=policy_body,policy_sha256=policy,source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},primary_analysis_sha256=sha(p/'analysis_sheng.json'),scope='Posthoc exploratory reused-data TASK FUNCTIONAL expiry calibration; standard max95 tolerance theorem under fixed-predictor iid law. Finite future occupancy grid only, no untouched holdout, continuous physics, conditional grant risk or novelty guarantee.')
    (p/'functional_sheng.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
