#!/usr/bin/env python3
"""Finite future-snapshot tube calibration; no future labels enter source paths."""
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
import evaluate as primary
from engine import replay
ROOT=primary.ROOT;HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geometry(cm,radius,ext,refused=False):
    if refused:return [dict(lower_us=0,upper_us=500000,reason='refused') for _ in range(2)]
    life=primary.module.life;body=math.ceil(float(np.linalg.norm(ext))*1e6);states=[life.State(int(c[0])*10000,int(c[1])*10000,radius+body,3000000,0) for c in cm];out=[]
    for qx in (-6000000,6000000):
        r=life.expiry(states,(qx,0),750000,500000,complete_support=True);low=r['safe_through_us'];up=low if r['reason']=='unsafe_at_observation' or r['capped'] else low+1;out.append(dict(lower_us=low,upper_us=up,reason=r['reason'],witness_index=r['witness_index']))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=json.loads((p/'analysis_sheng.json').read_bytes());eps=d['episodes'];byep={e['episode']['id']:e for e in eps};catalog=d['contract_body']['catalog'];bps=list(catalog);scores={k:0. for k in byep};paircounts={k:0 for k in byep}
    for r in d['rows']:
        if not r['available']:continue
        ep=byep[r['episode_id']];c=np.array(r['centers']);anchor=np.array(r['anchor']);road=np.array(r['road'])
        for state in ep['trajectory'][r['step']:r['step']+11]:
            dt=(state['step']-r['step'])*.05;true=(np.array(state['center'])-anchor)@road;score=max(0.,float(np.min(np.linalg.norm(c-true[:2],axis=1)))-3*dt);scores[r['episode_id']]=max(scores[r['episode_id']],score);paircounts[r['episode_id']]+=1
    registry={}
    for bp in bps:
        cal=[scores[e['episode']['id']] for e in eps if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(cal)==95;registry[bp]=dict(radius_um=math.ceil(max(cal)*1e6+1e-7)+8000,calibration_n=95,rank=95,slope_um_s=3000000)
    calibration=hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest();contract_body=dict(primary_contract=d['contract_body'],tube_protocol_sha256=sha(HERE/'TUBE_PROTOCOL.md'),future_scope='Six observed sources times11 future50ms snapshots; finite family only.');contract=hashlib.sha256(json.dumps(contract_body,sort_keys=True).encode()).hexdigest();messages=p/'tube_messages';messages.mkdir(exist_ok=False);out=[]
    for r in d['rows']:
        with np.load(p/'capture'/r['cloud_file']) as z:raw=z['raw'].copy();matrix=z['transform'].copy()
        source_buffer=np.zeros(r['original_points'],dtype=raw.dtype);source_buffer[::4]=raw
        bp=r['blueprint'];ext=catalog[bp];ci=bps.index(bp);radius=registry[bp]['radius_um'];anchor=np.array(r['anchor']);road=np.array(r['road']);reference=np.array(r['centers_cm'],dtype=np.int32).reshape(-1,2);bounds=geometry(reference,radius,ext,not r['available']);methods={}
        for method in ('union','lossless_centers','full_xyz'):
            samples=[];previous=None
            for repeat in range(3):
                start=time.perf_counter();selected=np.frombuffer(source_buffer.data,dtype=raw.dtype)[::4].copy();selection_done=time.perf_counter();xyz=np.c_[selected['x'],selected['y'],selected['z']].astype(float)
                if method!='full_xyz':c,_=primary.centers(xyz@matrix[:3,:3].T+matrix[:3,3],anchor,road,ext)
                if method=='union':wire=primary.encode(primary.quantized_centers(c),radius,r['frame'],r['timestamp'],ci,contract,calibration,not r['available'])
                else:wire=primary.pack_other(b'RXYZ' if method=='full_xyz' else b'LCEN',xyz if method=='full_xyz' else c,matrix,ci,r['frame'],r['timestamp'],contract,calibration)
                middle=time.perf_counter()
                if method=='union':decoded=primary.decode(wire,contract,calibration,ci,radius);cm=decoded['centers_cm'];refused=decoded['refused']
                else:cm=primary.unpack_other(wire,b'RXYZ' if method=='full_xyz' else b'LCEN',ci,contract,calibration,anchor,road,ext);refused=not len(cm)
                got=geometry(cm,radius,ext,refused);end=time.perf_counter();assert got==bounds
                if r['available']:assert np.array_equal(cm,reference)
                if previous is not None:assert previous==wire
                previous=wire;samples.append(dict(source_s=middle-start,receiver_s=end-middle,selection_s=selection_done-start))
            name=r['id']+'_'+method+'.bin';(messages/name).write_bytes(wire);methods[method]=dict(wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest(),packet='tube_messages/'+name,samples=samples,source_us=math.ceil(max(s['source_s'] for s in samples)*1e6),receiver_us=math.ceil(max(s['receiver_s'] for s in samples)*1e6))
        methods['fixed200']=dict(methods['union']);future_excluded=False
        if r['available']:
            for state in byep[r['episode_id']]['trajectory'][r['step']:r['step']+11]:
                true=(np.array(state['center'])-anchor)@road;dt=(state['step']-r['step'])*.05;future_excluded|=float(np.min(np.linalg.norm(reference/100.-true[:2],axis=1)))*1e6>radius+3000000*dt
        out.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,split=r['split'],step=r['step'],layout=r['layout'],frame=r['frame'],timestamp=r['timestamp'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],available=r['available'],centers_cm=r['centers_cm'],radius_um=radius,bounds=bounds,methods=methods,future_excluded=bool(future_excluded)))
        if len(out)%100==0:print('tube',len(out),flush=True)
    traces=[];summary=[]
    for bp in bps:
        ee=[e for e in eps if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in out if r['blueprint']==bp and r['split']=='test'];k=sum(any(r['future_excluded'] for r in rr if r['episode_id']==e['episode']['id']) for e in ee)
        summary.append(dict(blueprint=bp,**registry[bp],test_episodes=60,future_excluded_episodes=k,captured_frames=len(rr),available_frames=sum(r['available'] for r in rr)))
        for ep in ee:
            fr=[r for r in rr if r['episode_id']==ep['episode']['id']];t0=fr[0]['source_us'] if fr else 0
            for rate in (20000000,2000000):
                for method in ('union','lossless_centers','full_xyz','fixed200'):traces.append(dict(episode_id=ep['episode']['id'],blueprint=bp,bitrate=rate,method=method,**replay(fr,method,rate,t0)))
    deps=[HERE/n for n in ('tube.py','TUBE_PROTOCOL.md','engine.py','evaluate.py')];result=dict(registry=registry,calibration_scores=scores,pair_counts=paircounts,rows=out,traces=traces,summary=summary,calibration_sha256=calibration,contract_sha256=contract,contract_body=contract_body,primary_analysis_sha256=sha(p/'analysis_sheng.json'),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in deps},scope='Future-snapshot residual max95 tube calibration, slope3m/s is calibrated rather than physical velocity assumption. Independent current frame source paths and paid causal trace queues. Guarantee concerns only specified50ms future snapshots under iid finite episodes, not continuous physical safety.')
    (p/'tube_sheng.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
