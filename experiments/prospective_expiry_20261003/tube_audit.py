#!/usr/bin/env python3
"""Independent scalar future residuals, packet payload and linear contact audit."""
import argparse,hashlib,importlib.util,json,math,struct,zlib
from decimal import Decimal,ROUND_CEILING,localcontext
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_causal_audit',HERE/'audit.py');independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
PH=struct.Struct('<4sHHIIdI32s32s');OH=struct.Struct('<4sIIdI32s32s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def linear_horizon(cm,radius,ext,qx):
    rad=radius+math.ceil(math.sqrt(sum(x*x for x in ext))*1e6)+750000;best=(500000,500000)
    for c in cm:
        d2=(int(c[0])*10000-qx)**2+(int(c[1])*10000)**2
        if d2<=rad*rad:return 0,0
        with localcontext() as ctx:
            ctx.prec=80;t=(Decimal(d2).sqrt()-rad)/3
            if t>500000:lo=up=500000
            else:up=int(t.to_integral_value(rounding=ROUND_CEILING));lo=up-1
        assert d2>(rad+3*lo)**2 and (lo==500000 or d2<=(rad+3*(lo+1))**2)
        if lo<best[0]:best=(lo,up)
    return best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'tube_sheng.json');primary=read(p/'analysis_sheng.json');primaryaudit=read(p/'audit_sheng.json')
    assert d['primary_analysis_sha256']==primaryaudit['analysis_sha256']==sha(p/'analysis_sheng.json')
    for mapping in (read(HERE/'tube_freeze.json')['source_hashes'],d['source_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    catalog=primary['contract_body']['catalog'];bps=list(catalog);byep={e['episode']['id']:e for e in primary['episodes']};orig={r['id']:r for r in primary['rows']};scores={k:0. for k in byep};pairs={k:0 for k in byep};excluded={};future_pairs=0
    for r in primary['rows']:
        bad=False
        if r['available']:
            ep=byep[r['episode_id']];road=np.array(r['road']);anchor=np.array(r['anchor'])
            for state in ep['trajectory'][r['step']:r['step']+11]:
                future=(np.array(state['center'])-anchor)@road;age=(state['step']-r['step'])/20;res=max(0.,min(math.hypot(c[0]-future[0],c[1]-future[1]) for c in r['centers'])-3*age);scores[r['episode_id']]=max(scores[r['episode_id']],res);pairs[r['episode_id']]+=1;future_pairs+=1
        for k in ('source_us','acquisition_us','available','centers_cm'):
            assert next(x for x in d['rows'] if x['id']==r['id'])[k]==r[k]
    registry={}
    for bp in bps:
        cal=[scores[e['episode']['id']] for e in primary['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(cal)==95;registry[bp]=dict(radius_um=math.ceil(max(cal)*1e6+1e-7)+8000,calibration_n=95,rank=95,slope_um_s=3000000)
    assert registry==d['registry'] and pairs==d['pair_counts'];assert all(abs(scores[k]-d['calibration_scores'][k])<1e-10 for k in scores)
    calibration=hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest();contract=hashlib.sha256(json.dumps(d['contract_body'],sort_keys=True).encode()).hexdigest();assert calibration==d['calibration_sha256'] and contract==d['contract_sha256'];assert d['contract_body']['primary_contract']==primary['contract_body']
    ages=packets=0
    for fr in d['rows']:
        r=orig[fr['id']];radius=registry[r['blueprint']]['radius_um'];cm=np.array(r['centers_cm'],dtype=np.int32).reshape(-1,2);bad=False
        if r['available']:
            for state in byep[r['episode_id']]['trajectory'][r['step']:r['step']+11]:
                true=(np.array(state['center'])-r['anchor'])@np.array(r['road']);age=(state['step']-r['step'])/20;bad|=min(math.hypot(c[0]/100.-true[0],c[1]/100.-true[1]) for c in cm)*1e6>radius+3000000*age
        assert fr['future_excluded']==bad;excluded[fr['id']]=bad
        for q,qx in enumerate((-6000000,6000000)):
            lo,up=linear_horizon(cm,radius,catalog[r['blueprint']],qx) if r['available'] else (0,500000);b=fr['bounds'][q];assert (lo,up)==(b['lower_us'],b['upper_us']);ages+=1
        for method in ('union','lossless_centers','full_xyz'):
            m=fr['methods'][method];wire=(p/m['packet']).read_bytes();assert len(wire)==m['wire_bytes'] and sha(p/m['packet'])==m['wire_sha256'];oldwire=(p/r['methods'][method]['packet']).read_bytes()
            if method=='union':
                assert hashlib.sha256(wire[:-32]).digest()==wire[-32:];h=PH.unpack(wire[:PH.size]);oldh=PH.unpack(oldwire[:PH.size]);assert h[:6]==oldh[:6] and h[6]==(radius if r['available'] else 0) and h[7].hex()==contract and h[8].hex()==calibration
                assert wire[PH.size:-32]==oldwire[PH.size:-32]
            else:
                blob=zlib.decompress(wire);oldblob=zlib.decompress(oldwire);assert hashlib.sha256(blob[:-32]).digest()==blob[-32:];h=OH.unpack(blob[:OH.size]);oldh=OH.unpack(oldblob[:OH.size]);assert h[:5]==oldh[:5] and h[5].hex()==contract and h[6].hex()==calibration and blob[OH.size:-32]==oldblob[OH.size:-32]
            assert len(m['samples'])==3 and all(all(math.isfinite(v) and v>=0 for v in s.values()) for s in m['samples']);assert m['source_us']==math.ceil(max(s['source_s'] for s in m['samples'])*1e6) and m['receiver_us']==math.ceil(max(s['receiver_s'] for s in m['samples'])*1e6);packets+=1
    checks=[]
    for tr in d['traces']:
        rr=[r for r in d['rows'] if r['episode_id']==tr['episode_id']];t0=rr[0]['source_us'] if rr else 0;expected=independent.queues(rr,tr['method'],tr['bitrate'],t0)
        for k,v in expected.items():assert tr[k]==v
        hits=0
        for decision in tr['decisions']:
            if not decision['grant']:continue
            r=orig[decision['fact_id']];bp=r['blueprint'];body=math.ceil(math.sqrt(sum(x*x for x in catalog[bp]))*1e6)/1e6;qx=(-6.,6.)[decision['query']];end=decision['now_us']+220000;occupied=False
            assert end<=decision['deadline_us']<=r['source_us']+500000
            for state in byep[tr['episode_id']]['trajectory']:
                if not decision['now_us']<=math.floor(state['timestamp']*1e6)<=end:continue
                true=(np.array(state['center'])-r['anchor'])@np.array(r['road']);occupied|=math.hypot(true[0]-qx,true[1])<=body+.75
            if occupied:assert excluded[r['id']]
            hits+=occupied
        checks.append(dict(episode_id=tr['episode_id'],blueprint=tr['blueprint'],method=tr['method'],bitrate=tr['bitrate'],grants=tr['grants'],wire_bytes=tr['wire_bytes'],scheduled_queries=32,observed_disc_occupied_grants=hits))
    summary=[]
    for bp in bps:
        test=[e for e in primary['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in d['rows'] if r['blueprint']==bp and r['split']=='test'];k=sum(any(excluded[r['id']] for r in rr if r['episode_id']==e['episode']['id']) for e in test);s=dict(blueprint=bp,**registry[bp],test_episodes=60,future_excluded_episodes=k,captured_frames=len(rr),available_frames=sum(r['available'] for r in rr));assert s==next(c for c in d['summary'] if c['blueprint']==bp);summary.append(dict(**s,one_sided_95_risk_upper=independent.old.risk_upper(k,60)))
    result=dict(summary=summary,trace_checks=checks,future_pairs=future_pairs,packet_checks=packets,analytic_age_checks=ages,source_sha256=sha(Path(__file__)),tube_sha256=sha(p/'tube_sheng.json'),primary_audit_sha256=sha(p/'audit_sheng.json'),scope='Independent scalar max95 future-SNAPSHOT prediction residuals, linear analytic integer contact, exact primary-validated payloads and paid delivered-prefix trace decisions. No physical continuous motion or live ego-control guarantee.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('summary','trace_checks')}))
if __name__=='__main__':main()
