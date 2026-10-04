#!/usr/bin/env python3
"""Deadline-only necessary-context sensitivity; same actual primary source jobs.

Source encoding/bytes/fees are unchanged and reused, not nominal estimates.
Only necessary receiver registration and actual decoder profiles change.
This is not a newly simultaneous end-to-end performance experiment.
"""
import hashlib,json,math,time,zlib,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
sys.path.insert(0,str(ROOT/'experiments/body_expiry_20261004'))
from engine import replay
FAMILIES=('joint','ridge','local_mean','local_modes')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
def compress(obj):
    b=canon(obj);return zlib.compress(b+hashlib.sha256(b).digest(),6)
def expand(wire):
    b=zlib.decompress(wire);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:];return json.loads(b[:-32])
def registration(paid):
    ctx=paid['registration'];return dict(version=1,primary_contract=paid['contract_sha256'],calibration=ctx['calibration_sha256'],calibration_receipt_sha256=ctx['calibration_receipt_sha256'],catalog_sha256=hashlib.sha256(canon(ctx['catalog'])).hexdigest(),blueprints=list(ctx['catalog']),families=list(FAMILIES),queries_um=ctx['queries_um'],cap_us=ctx['cap_us'],query_radius_um=ctx['query_radius_um'],motion=ctx['motion'],model_freeze_sha256=ctx['model_freeze_sha256'],receiver_service_sha256=sha(Path(__file__)))
def setup_decode(wire,approved_hash):
    ctx=expand(wire);assert hashlib.sha256(canon(ctx)).hexdigest()==approved_hash and ctx['version']==1 and ctx['families']==list(FAMILIES) and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['cap_us']==500000 and ctx['query_radius_um']==750000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000) and ctx['receiver_service_sha256']==sha(Path(__file__));return ctx
def decode(wire,family,ctx):
    obj=expand(wire);assert obj['version']==1 and obj['kind']=='deadline' and obj['family']==family and family in ctx['families'];assert obj['contract']==ctx['primary_contract'] and obj['calibration']==ctx['calibration'] and obj['blueprint'] in ctx['blueprints'] and obj['layout'] in (0,1)
    assert obj['status'] in ('bounded','refused','empty') and len(obj['lower_us'])==(2 if obj['status']=='bounded' else 0)
    assert all(type(v) is int and 0<=v<=500000 for v in obj['lower_us']) and all(type(obj[k]) is int and obj[k]>=0 for k in ('frame','source_us'))
    return {k:obj[k] for k in ('status','lower_us','blueprint','layout','frame','source_us')}
def main():
    f=read(E/'minimal_registration_freeze.json')
    for sec in ('sources','inputs'):
        for n,h in f[sec].items():assert sha(ROOT/n)==h,n
    assert (P/'evaluation_terminal.txt').read_text()=='FINITE_EVALUATION_AND_AUDIT_COMPLETE\n' and not (P/'minimal_registration_sheng.json').exists()
    paid=read(P/'paid_sheng.json');ctx=registration(paid);approved=hashlib.sha256(canon(ctx)).hexdigest();samples=[]
    for _ in range(3):
        t=time.perf_counter();wire=compress(ctx);ss=time.perf_counter()-t;t=time.perf_counter();assert setup_decode(wire,approved)==ctx;rx=time.perf_counter()-t;samples.append(dict(source_s=ss,receiver_s=rx))
    (P/'minimal_setup.bin').write_bytes(wire);setup=dict(samples=samples,wire_bytes=len(wire),wire_sha256=sha(P/'minimal_setup.bin'),source_us=math.ceil(max(v['source_s'] for v in samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6));rows=[];byep=defaultdict(list)
    for i,r in enumerate(paid['rows']):
        seq=sorted(FAMILIES,key=lambda m:hashlib.sha256((r['id']+'|minimal_rx|'+m).encode()).digest());methods={}
        for family in seq:
            key=family+'_deadline';old=r['methods'][key];wire=(ROOT/old['packet']).read_bytes();assert len(wire)==old['wire_bytes'] and sha(ROOT/old['packet'])==old['wire_sha256'];ss=[]
            for v in old['samples']:
                t=time.perf_counter();out=decode(wire,family,ctx);rx=time.perf_counter()-t;assert (out['status'],out['lower_us'])==(old['status'],old['lower_us']) and all(out[k]==r[k] for k in ('blueprint','layout','frame','source_us'));ss.append(dict(source_s=v['source_s'],receiver_s=rx,selection_s=v['selection_s']))
            methods[key]=dict(old);methods[key].update(samples=ss,receiver_us=math.ceil(max(v['receiver_s'] for v in ss)*1e6))
        item={k:r[k] for k in ('id','episode_id','blueprint','layout','frame','source_us','acquisition_us','selection_s')};item.update(methods=methods,receiver_measurement_order=seq);rows.append(item);byep[r['episode_id']].append(item)
        if (i+1)%300==0:print('minimal context receiver',i+1,flush=True)
    d=read(P/'qualification_sheng.json');traces=[]
    for ep in d['episodes']:
        e=ep['episode']
        if e['split']!='test':continue
        rr=byep[e['id']];t0=min(r['source_us'] for r in rr) if rr else 0
        for family in FAMILIES:
            for rate in (20000000,2000000):
                for startup in ('warm','cold'):traces.append(dict(episode_id=e['id'],blueprint=e['blueprint'],capture_status=ep['status'],method=family+'_deadline',rate=rate,startup=startup,t0=t0,**replay(rr,family+'_deadline',rate,t0,setup if startup=='cold' else None)))
    out=dict(rows=rows,traces=traces,setup=setup,registration=ctx,registration_sha256=approved,paid_sha256=sha(P/'paid_sheng.json'),qualification_sha256=sha(P/'qualification_sheng.json'),primary_audit_sha256=sha(P/'audit_sheng.json'),freeze_sha256=sha(E/'minimal_registration_freeze.json'),scope='Necessary deadline-only receiver context. Same already measured full primary source fees/actual packet bytes/ages, newly paid decoder/setup fees. Context/decoder sensitivity, not newly simultaneous source/function timing, source attestation, new model/risk fit or live radio.');(P/'minimal_registration_sheng.json').write_text(json.dumps(out,separators=(',',':'))+'\n');print('FINITE_MINIMAL_CONTEXT_COMPLETE',flush=True)
if __name__=='__main__':main()
