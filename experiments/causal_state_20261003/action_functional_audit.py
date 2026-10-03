#!/usr/bin/env python3
"""Independent task-contact integer residual, payload, queue and gap audit."""
import argparse,hashlib,importlib.util,json,math,statistics
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('tube_independent',HERE/'tube_audit.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def contact(r,ep,ext):
    body=math.ceil(math.sqrt(sum(v*v for v in ext))*1e6)/1e6;out=[]
    for q in (-6.,6.):
        g=500000
        for t in ep['trajectory'][r['step']:r['step']+11]:
            d=[t['center'][i]-r['anchor'][i] for i in range(3)];x=sum(d[i]*r['road'][i][0] for i in range(3));y=sum(d[i]*r['road'][i][1] for i in range(3))
            if math.hypot(x-q,y)<=body+.75:g=max(-1,math.floor(t['timestamp']*1e6)-r['source_us']-1);break
        out.append(g)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'action_functional_sheng.json');primary=read(p/'analysis_sheng.json');audit=read(p/'audit_sheng.json');assert d['primary_analysis_sha256']==audit['analysis_sha256']==sha(p/'analysis_sheng.json')
    for mapping in (d['source_hashes'],read(HERE/'action_functional_freeze.json')['source_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    catalog=primary['contract_body']['catalog'];byep={e['episode']['id']:e for e in primary['episodes']};orig={r['id']:r for r in primary['rows']};scores={k:0 for k in byep};records={};packets=ages=0
    for r in primary['rows']:
        cm=np.asarray(r['centers_cm'],dtype=np.int32).reshape(-1,2);h=[old.linear_horizon(cm,8000,catalog[r['blueprint']],q)[0] if r['available'] else 0 for q in (-6000000,6000000)];g=contact(r,byep[r['episode_id']],catalog[r['blueprint']]);records[r['id']]=dict(h=h,g=g)
        if r['available']:scores[r['episode_id']]=max(scores[r['episode_id']],max([max(0,x-y) for x,y in zip(h,g) if x>=220000]+[0]))
    registry={bp:dict(correction_us=max(scores[e['episode']['id']] for e in primary['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'),calibration_n=95,rank=95) for bp in catalog};assert registry==d['registry'] and scores==d['episode_scores'];assert d['policy_body']['registry']==registry and d['policy_body']['primary_contract_sha256']==primary['contract_sha256'] and d['policy_body']['primary_calibration_sha256']==primary['calibration_sha256'] and d['policy_body']['protocol_sha256']==sha(HERE/'ACTION_FUNCTIONAL_PROTOCOL.md');assert hashlib.sha256(json.dumps(d['policy_body'],sort_keys=True).encode()).hexdigest()==d['policy_sha256']
    violations={};slacks={bp:[] for bp in catalog};positive_slacks={bp:[] for bp in catalog};over={bp:[] for bp in catalog}
    for r in d['rows']:
        ref=orig[r['id']];rec=records[r['id']];delta=registry[r['blueprint']]['correction_us'];l=[max(-1,h-delta) if h>=220000 else -1 for h in rec['h']];assert rec['g']==r['grid_oracle_us'] and l==[b['lower_us'] for b in r['bounds']];assert rec['h']==[b['lower_us'] for b in r['base_bounds']];ages+=2
        for k in ('episode_id','blueprint','split','step','layout','source_us','acquisition_us','available'):assert r[k]==ref[k]
        bad=r['available'] and any(x>y for x,y in zip(l,rec['g']));assert bad==r['deadline_overstatement'];violations[r['id']]=bad
        if r['split']=='test' and r['available']:
            for x,y in zip(l,rec['g']):
                slacks[r['blueprint']].append(max(0,y-x));over[r['blueprint']].append(max(0,x-y))
                if x>=220000:positive_slacks[r['blueprint']].append(max(0,y-x))
        for method in ('union','lossless_centers','full_xyz'):
            m=r['methods'][method];refm=ref['methods'][method];assert all(m[k]==refm[k] for k in ('packet','wire_bytes','wire_sha256','source_us'));wire=p/m['packet'];assert wire.stat().st_size==m['wire_bytes'] and sha(wire)==m['wire_sha256'];assert len(m['samples'])==3
            for s,t in zip(m['samples'],refm['samples']):assert s['source_s']==t['source_s'] and s['selection_s']==t['selection_s'] and math.isfinite(s['receiver_s']) and s['receiver_s']>=0
            assert m['receiver_us']==math.ceil(max(s['receiver_s'] for s in m['samples'])*1e6);packets+=1
    checked=[]
    for tr in d['traces']:
        rows=[r for r in d['rows'] if r['episode_id']==tr['episode_id']];t0=rows[0]['source_us'] if rows else 0;expected=old.independent.queues(rows,tr['method'],tr['bitrate'],t0)
        for k,v in expected.items():assert tr[k]==v,(tr['episode_id'],k)
        oracle=[dict(r,bounds=[dict(lower_us=g if h>=220000 else -1) for h,g in zip(records[r['id']]['h'],records[r['id']]['g'])]) for r in rows];og=old.independent.queues(oracle,tr['method'],tr['bitrate'],t0)['grants'];assert og==tr['oracle_grants'];unsafe=0
        for dec in tr['decisions']:
            if not dec['grant']:continue
            r=orig[dec['fact_id']];body=math.ceil(math.sqrt(sum(v*v for v in catalog[r['blueprint']]))*1e6)/1e6;qx=(-6.,6.)[dec['query']];hit=False;end=dec['now_us']+220000;assert end<=dec['deadline_us']<=r['source_us']+500000
            for t in byep[tr['episode_id']]['trajectory']:
                if not dec['now_us']<=math.floor(t['timestamp']*1e6)<=end:continue
                dx=[t['center'][i]-r['anchor'][i] for i in range(3)];x=sum(dx[i]*r['road'][i][0] for i in range(3));y=sum(dx[i]*r['road'][i][1] for i in range(3));hit|=math.hypot(x-qx,y)<=body+.75
            if hit:assert violations[r['id']]
            unsafe+=hit
        checked.append(dict(episode_id=tr['episode_id'],blueprint=tr['blueprint'],method=tr['method'],bitrate=tr['bitrate'],grants=tr['grants'],scheduled_queries=32,wire_bytes=tr['wire_bytes'],oracle_grants=og,observed_disc_occupied_grants=unsafe))
    summary=[]
    for bp in catalog:
        test=[e for e in primary['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in d['rows'] if r['blueprint']==bp and r['split']=='test'];k=sum(any(violations[r['id']] for r in rr if r['episode_id']==e['episode']['id']) for e in test);s=dict(blueprint=bp,**registry[bp],test_episodes=60,deadline_overstatement_episodes=k);assert s==next(x for x in d['summary'] if x['blueprint']==bp);v=slacks[bp];pv=positive_slacks[bp];summary.append(dict(**s,one_sided_95_risk_upper=old.independent.old.risk_upper(k,60),test_available_source_query_pairs=len(v),median_positive_slack_us=statistics.median(v) if v else None,mean_positive_slack_us=sum(v)/len(v) if v else None,max_positive_slack_us=max(v+[0]),pairs_with_slack_at_most_10ms=sum(x<=10000 for x in v),max_overstatement_us=max(over[bp]+[0]),geometrically_220ms_eligible_pairs=len(pv),eligible_median_positive_slack_us=statistics.median(pv) if pv else None))
    result=dict(summary=summary,trace_checks=checked,packet_checks=packets,analytic_age_checks=ages,source_sha256=sha(Path(__file__)),action_functional_sha256=sha(p/'action_functional_sheng.json'),primary_audit_sha256=sha(p/'audit_sheng.json'),scope='Independent Decimal current geometry, integer future-grid contact/correction, same primary-validated messages, charged queues and oracle gap. Reused posthoc data, finite declared body-disc snapshot contact; no untouched holdout or continuous physical safety/novelty proof.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
