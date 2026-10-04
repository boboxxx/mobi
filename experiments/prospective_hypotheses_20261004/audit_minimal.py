#!/usr/bin/env python3
"""Independent minimum-context bytes, unchanged source jobs and FIFO sensitivity."""
import argparse,hashlib,importlib.util,json,math,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
spec=importlib.util.spec_from_file_location('minimum_independent_body',ROOT/'experiments/body_expiry_20261004/audit.py');body=importlib.util.module_from_spec(spec);spec.loader.exec_module(body)
FAMILIES=('joint','ridge','local_mean','local_modes')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
def expand(w):
    b=zlib.decompress(w);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:];return json.loads(b[:-32])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();f=read(E/'minimal_registration_freeze.json')
    for sec in ('sources','inputs'):
        for n,h in f[sec].items():assert sha(ROOT/n)==h,n
    d=read(P/'minimal_registration_sheng.json');paid=read(P/'paid_sheng.json');qualified=read(P/'qualification_sheng.json');assert d['paid_sha256']==sha(P/'paid_sheng.json') and d['qualification_sha256']==sha(P/'qualification_sheng.json') and d['primary_audit_sha256']==sha(P/'audit_sheng.json') and d['freeze_sha256']==sha(E/'minimal_registration_freeze.json')
    primary=paid['registration'];ctx=dict(version=1,primary_contract=paid['contract_sha256'],calibration=primary['calibration_sha256'],calibration_receipt_sha256=primary['calibration_receipt_sha256'],catalog_sha256=hashlib.sha256(canon(primary['catalog'])).hexdigest(),blueprints=list(primary['catalog']),families=list(FAMILIES),queries_um=primary['queries_um'],cap_us=primary['cap_us'],query_radius_um=primary['query_radius_um'],motion=primary['motion'],model_freeze_sha256=primary['model_freeze_sha256'],receiver_service_sha256=sha(E/'minimal_registration.py'));assert d['registration']==ctx and d['registration_sha256']==hashlib.sha256(canon(ctx)).hexdigest()
    s=d['setup'];wire=(P/'minimal_setup.bin').read_bytes();assert expand(wire)==ctx and len(wire)==s['wire_bytes'] and sha(P/'minimal_setup.bin')==s['wire_sha256'] and len(s['samples'])==3
    for dest,key in (('source_us','source_s'),('receiver_us','receiver_s')):assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
    old={r['id']:r for r in paid['rows']};assert [r['id'] for r in d['rows']]==list(old);byep=defaultdict(list);packets=0
    for r in d['rows']:
        original=old[r['id']]
        for key in ('id','episode_id','blueprint','layout','frame','source_us','acquisition_us','selection_s'):assert r[key]==original[key]
        assert r['receiver_measurement_order']==sorted(FAMILIES,key=lambda m:hashlib.sha256((r['id']+'|minimal_rx|'+m).encode()).digest()) and set(r['methods'])=={m+'_deadline' for m in FAMILIES}
        for method,m in r['methods'].items():
            prev=original['methods'][method];assert {k:v for k,v in m.items() if k not in ('samples','receiver_us')}=={k:v for k,v in prev.items() if k not in ('samples','receiver_us')};assert len(m['samples'])==3
            for sample,prior in zip(m['samples'],prev['samples']):assert sample['source_s']==prior['source_s'] and sample['selection_s']==prior['selection_s'] and sample['receiver_s']>=0
            assert m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);path=ROOT/m['packet'];wire=path.read_bytes();assert sha(path)==m['wire_sha256'] and len(wire)==m['wire_bytes'];obj=expand(wire);family=method[:-9];assert family in FAMILIES
            expected=dict(version=1,kind='deadline',family=family,blueprint=r['blueprint'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],contract=paid['contract_sha256'],calibration=ctx['calibration'],status=m['status'],lower_us=m['lower_us']);assert obj==expected;packets+=1
        byep[r['episode_id']].append(r)
    episodes={e['episode']['id']:e for e in qualified['episodes'] if e['episode']['split']=='test'};assert len(episodes)==360 and len(d['traces'])==360*4*4;seen=set();totals=defaultdict(int)
    for tr in d['traces']:
        key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);assert tr['method'] in {m+'_deadline' for m in FAMILIES} and tr['rate'] in (20000000,2000000) and tr['startup'] in ('warm','cold');ep=episodes[tr['episode_id']];assert tr['capture_status']==ep['status'] and tr['blueprint']==ep['episode']['blueprint'];rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['t0']==t0;expected=body.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==v for k,v in expected.items());totals[tr['method']+'|'+str(tr['rate'])+'|'+tr['startup']]+=tr['grants']
    out=dict(rows=len(d['rows']),actual_packet_checks=packets,trace_checks=len(d['traces']),decision_checks=len(d['traces'])*32,grants=dict(totals),setup_bytes=s['wire_bytes'],source_jobs_and_packet_bytes_unchanged=True,minimal_registration_sha256=sha(P/'minimal_registration_sheng.json'),primary_paid_sha256=sha(P/'paid_sheng.json'),source_sha256=sha(Path(__file__)),scope='Independent wire and FIFO verification; original measured source jobs reused, new minimal receiver/setup costs. Context/decoder sensitivity only, not simultaneous new end-to-end measurement or new risk/geometry qualification.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('FINITE_MINIMUM_CONTEXT_AUDIT_COMPLETE',flush=True)
if __name__=='__main__':main()
