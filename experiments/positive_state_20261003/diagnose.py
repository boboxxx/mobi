#!/usr/bin/env python3
"""Post-evaluation diagnostics; no threshold or policy is changed."""
import argparse,hashlib,importlib.util,json,math,struct,zlib
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from audit import proposals
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def contains(cm,radius,xy):
    with localcontext() as ctx:
        ctx.prec=80
        x,y=[Decimal.from_float(float(v))*1000000 for v in xy]
        return any((x-int(c[0])*10000)**2+(y-int(c[1])*10000)**2<=int(radius)**2 for c in cm)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();data=json.loads((p/'analysis_sheng.json').read_bytes());catalog=data['contract_body']['catalog'];checks=[]
    for r in data['rows']:
        if r['split']!='test':continue
        body=math.ceil(float(np.linalg.norm(catalog[r['blueprint']]))*1e6);unsafe=[]
        for j,qx in enumerate((-6000000,6000000)):
            if not r['modeled_remaining_us'][j]:continue
            with localcontext() as ctx:
                ctx.prec=80;x=Decimal.from_float(float(r['true_xy'][0]))*1000000-qx;y=Decimal.from_float(float(r['true_xy'][1]))*1000000;t=Decimal(r['cost_us'])/1000000;reach=body+750000+5000000*t+1500000*t*t;hit=x*x+y*y<=reach*reach
            if hit:assert not r['covered'];unsafe.append(j)
        checks.append(dict(id=r['id'],episode=r['episode'],blueprint=r['blueprint'],covered=r['covered'],positive_queries=[j for j,n in enumerate(r['modeled_remaining_us']) if n>0],true_disc_reachable_by_charged_deadline=unsafe))
    bankpath=ROOT/'results/nominal_witness_20261003/transfer_sheng.json';bank=json.loads(bankpath.read_bytes());fixed=json.loads((ROOT/'results/proof_repair_20261003/replay/rows.json').read_bytes());sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};header=struct.Struct('<4sHHIIHHd16d32sI');old=ROOT/'results/tube_evidence_20261003/replay';regression=[];cached={}
    for row in bank['rows']:
        original=next(r for r in fixed if r['budget']==4096 and (r['blueprint'],r['query_index'],r['radius_um'])==(row['blueprint'],row['query_index'],row['radius_um']));name=original['current_packet'];bp=row['blueprint'];source=sources[original['old_case']]
        if name not in cached:
            wire=zlib.decompress((old/name).read_bytes());assert hashlib.sha256(wire[:-32]).digest()==wire[-32:];h=header.unpack(wire[:header.size]);xyz=np.frombuffer(wire,dtype='<f4',count=h[25]*3,offset=header.size).reshape(-1,3);raw=np.empty(len(xyz),dtype=[('x','<f4'),('y','<f4'),('z','<f4')]);raw['x'],raw['y'],raw['z']=xyz.T;matrix=np.array(h[8:24]).reshape(4,4);road=np.array(source['road_rotation']);yaw=math.atan2(road[1,0],road[0,0]);c,meta=proposals(raw,matrix,np.array(source['anchor']),yaw,catalog[bp]);cached[name]=dict(cm=np.rint(c*100).astype(np.int32),meta=meta,sha256=sha(old/name))
        f=cached[name];radius=data['registry'][bp]['radius_um'];keep=[i for i,b in enumerate(bank['pools'][bp]) if contains(f['cm'],radius,b['pose'][:2])];original_best=row['best_nominal_pool_index'];raw_best=row['best_actual_pool_index'];regression.append(dict(blueprint=bp,query_index=row['query_index'],sigma=row['sigma'],radius_um=row['radius_um'],current_packet=name,current_packet_sha256=f['sha256'],positive_centers_cm=f['cm'].tolist(),positive_radius_um=radius,candidates=len(bank['pools'][bp]),retained_indices=keep,old_best_nominal_retained=original_best in keep,old_best_actual_retained=raw_best in keep,scope='Old single-view regression, not independent coverage and not authorization under the fresh two-view availability rule.'))
    result=dict(test_query_diagnostics=checks,positive_test_query_results=sum(len(x['positive_queries']) for x in checks),true_disc_reachable_positive_queries=sum(len(x['true_disc_reachable_by_charged_deadline']) for x in checks),true_disc_reachable_positive_episodes=len({x['episode'] for x in checks if x['true_disc_reachable_by_charged_deadline']}),regression=regression,old_best_nominal_retained=sum(r['old_best_nominal_retained'] for r in regression),old_best_actual_retained=sum(r['old_best_actual_retained'] for r in regression),source_sha256=sha(Path(__file__)),bank_sha256=sha(bankpath),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Post-evaluation diagnostic only. Positive outputs are checked against ground-truth center reachability under the same abstract disc/motion model at the charged deadline, not observed physical collisions. Frozen old candidates are tested as regression using actual old raw coordinates; no tuning, independent holdout or old-family authorization claim.')
    a.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
