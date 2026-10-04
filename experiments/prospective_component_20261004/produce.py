#!/usr/bin/env python3
"""Paid full-XYZ profiles and matched function/deadline FIFO reconstruction."""
import bootstrap
import hashlib,math,time,sys,argparse
from collections import defaultdict
from fresh_io import ROOT,E,P,sha,read,write,canon,freeze_check,load,frontend
from scores import load_models
from fresh_inference import PRIMARY,state,compact
from fresh_transport import KINDS,registration,compress,decode_setup,encode,decode
sys.path.insert(0,str(ROOT/'experiments/body_expiry_20261004'))
from engine import replay
METHODS=tuple(f+'_'+k for f in PRIMARY for k in KINDS)
def order(identity,iteration):return sorted(METHODS,key=lambda m:hashlib.sha256((identity+'|'+str(iteration)+'|'+m).encode()).digest())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',choices=('certification','test'),required=True);args=ap.parse_args();split=args.split;freeze_check()
    paid_output=P/('paid_'+split+'_sheng.json');messages=P/('messages_'+split);assert not paid_output.exists() and not messages.exists()
    d=read(P/('qualification_'+split+'_sheng.json'));receipt=read(P/'calibration_frozen.json');assert d['registry']==receipt['registry'] and d['calibration_receipt_sha256']==sha(P/'calibration_frozen.json')
    f=read(E/'freeze.json');ctx=registration(d,sha(P/'calibration_frozen.json'),f);contract=hashlib.sha256(canon(ctx)).hexdigest();models=load_models();bg=read(ROOT/'results/background_frontend_20261004/background.json');samples=[]
    for _ in range(3):
        t=time.perf_counter();wire=compress(ctx);ss=time.perf_counter()-t;t=time.perf_counter();assert decode_setup(wire,contract)==ctx;rx=time.perf_counter()-t;samples.append(dict(source_s=ss,receiver_s=rx))
    (P/('setup_'+split+'.bin')).write_bytes(wire);setup=dict(samples=samples,wire_bytes=len(wire),wire_sha256=sha(P/('setup_'+split+'.bin')),source_us=math.ceil(max(v['source_s'] for v in samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6));messages.mkdir();rows=[];byep=defaultdict(list)
    for j,r in enumerate(v for v in d['rows'] if v['split']==split):
        raw,T,path=load(r);bp=r['blueprint'];ext=ctx['catalog'][bp];profiles={m:[] for m in METHODS};wires={};outs={};measurement_order=[]
        for iteration in range(3):
            sequence=order(r['id'],iteration);measurement_order.append(sequence)
            for method in sequence:
                family,kind=method.rsplit('_',1);start=time.perf_counter();gg,hh=frontend(raw,T,ext,d['basis'],bg,r['layout']);hyp=state(hh,r['layout'],bp,models,family);wire=encode(r,family,kind,hh,hyp,ctx,contract);ss=time.perf_counter()-start
                start=time.perf_counter();out=decode(wire,family,kind,ctx,contract);rx=time.perf_counter()-start
                assert hh==r['hulls_cm'] and gg==r['groups_cm'] and {k:out[k] for k in ('status','lower_us')}==compact(r['geometries'][family])
                assert all(out[k]==r[k] for k in ('blueprint','layout','frame','source_us'));assert method not in wires or wires[method]==wire
                profiles[method].append(dict(source_s=ss,receiver_s=rx,selection_s=r['selection_s']));wires[method]=wire;outs[method]=out
        methods={}
        for method in METHODS:
            target=messages/(r['id']+'_'+method+'.bin');target.write_bytes(wires[method]);pp=profiles[method];methods[method]=dict(**compact(outs[method]),samples=pp,source_us=math.ceil((max(v['source_s'] for v in pp)+r['selection_s'])*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in pp)*1e6),wire_bytes=len(wires[method]),wire_sha256=sha(target),packet=str(target.relative_to(ROOT)))
        item={k:r[k] for k in ('id','episode_id','blueprint','cloud_file','cloud_sha256','layout','frame','source_us','acquisition_us','selection_s')};item.update(split=r['split'],methods=methods,measurement_order=measurement_order);rows.append(item);byep[r['episode_id']].append(item)
        if (j+1)%200==0:print('paid',j+1,flush=True)
    traces=[]
    for ep in d['episodes']:
        e=ep['episode']
        if e['split']!=split:continue
        rr=byep[e['id']];t0=min(r['source_us'] for r in rr) if rr else 0
        for method in METHODS:
            for rate in (20000000,2000000):
                for startup in ('warm','cold'):traces.append(dict(episode_id=e['id'],blueprint=e['blueprint'],capture_status=ep['status'],split=e['split'],selected_query_index=e.get('selected_query_index'),method=method,rate=rate,startup=startup,t0=t0,**replay(rr,method,rate,t0,setup if startup=='cold' else None)))
    assert len(traces)==(600 if split=='certification' else 360)*len(METHODS)*4
    write(paid_output,dict(rows=rows,traces=traces,setup=setup,registration=ctx,contract_sha256=contract,qualification_sha256=sha(P/('qualification_'+split+'_sheng.json')),calibration_receipt_sha256=sha(P/'calibration_frozen.json'),measurement_freeze_sha256=sha(E/'freeze.json'),scope='Three actual full-XYZ/frontend/hull/predict/encode and receiver profiles per method, deterministic shuffled order, captured stride-copy fee. Maxima are measured fees, not WCET. Necessary lightweight shared context; initialized honest-source services; fixed queries, measured FIFO simulation, not live radio or ego policy.'));print('FINITE_PAID_HYPOTHESES_COMPLETE',len(rows),len(traces),flush=True)
if __name__=='__main__':main()
