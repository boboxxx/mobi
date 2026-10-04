#!/usr/bin/env python3
"""One new max125 episode qualification; calibration receipt precedes test reads."""
from collections import defaultdict
from fractions import Fraction as F
from scores import FAMILIES,load_models,predictions,current_scores
from io_common import ROOT,E,P,read,write,sha,canon,freeze_check,observed_record
from inference import state,infer,PRIMARY,DIAGNOSTICS
from integer_state import oracle_age,body_um
def main():
    freeze_check();assert (P/'capture_terminal.txt').read_text()=='FRESH_HYPOTHESES_CAPTURE_COMPLETE\n';assert read(P/'server_stopped.json')['stopped']
    assert not (P/'calibration_frozen.json').exists() and not (P/'qualification_sheng.json').exists()
    plan=read(E/'plan.json');records=read(P/'capture/record.json');episodes=read(P/'capture/episodes.json');assert len(plan)==1110 and [e['episode'] for e in episodes]==plan
    catalog=read(E/'catalog.json');bg=read(ROOT/'results/background_frontend_20261004/background.json');basis=bg['basis'];models=load_models();scores=defaultdict(lambda:F(0));rows=[];inputs={}
    # Six source scans are one score event per entire planned episode.
    for i,r in enumerate(v for v in records if v['split']=='calibration'):
        rr=observed_record(r,catalog,basis,bg);local,centre=predictions(rr['hulls_cm'],r['layout'],r['blueprint'],models);ss=current_scores(rr['hulls_cm'],catalog[r['blueprint']],local,centre,rr['true_xy']);rr.update(prediction=local,ridge_center_um=centre,scores={m:[v.numerator,v.denominator] for m,v in ss.items()});rows.append(rr);inputs[str((P/'capture'/r['cloud_file']).relative_to(ROOT))]=r['cloud_sha256']
        for m,v in ss.items():scores[(r['episode_id'],m)]=max(scores[(r['episode_id'],m)],v)
        if (i+1)%500==0:print('calibration scored',i+1,flush=True)
    registry={}
    for bp in catalog:
        eps=[e for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(eps)==125;registry[bp]={}
        for m in FAMILIES:
            q=max(scores[(e['id'],m)] for e in eps);registry[bp][m]=[q.numerator,q.denominator]
    calibration=__import__('hashlib').sha256(canon(registry)).hexdigest();receipt=dict(registry=registry,calibration_sha256=calibration,calibration_episode_scores={e['id']:{m:[scores[(e['id'],m)].numerator,scores[(e['id'],m)].denominator] for m in FAMILIES} for e in plan if e['split']=='calibration'},input_hashes=inputs,model_freeze_sha256=sha(E/'freeze.json'),measurement_freeze_sha256=sha(E/'measurement_freeze.json'),calibration_n_per_class=125,whole_episode_exclusion_risk_target=.05,simultaneous_family_class_count=24,calibration_confidence_lower=1-24*.95**125,scope='Fixed scores and models before independent capture. Risk is for planned complete episodes under the fixed known-class law, not conditional on grants or location.')
    write(P/'calibration_frozen.json',receipt);receipt_sha=sha(P/'calibration_frozen.json');write(P/'qualification_order.json',dict(calibration_receipt_sha256=receipt_sha,test_clouds_read=0,receipt_written_before_test_processing=True));print('REGISTRY_FROZEN_BEFORE_TEST',calibration,flush=True)
    for i,r in enumerate(v for v in records if v['split']=='test'):
        rr=observed_record(r,catalog,basis,bg);bp=r['blueprint'];hh=rr['hulls_cm'];extent=catalog[bp];local,centre=predictions(hh,r['layout'],bp,models);ss=current_scores(hh,extent,local,centre,rr['true_xy']);geometries={}
        for m in PRIMARY:geometries[m]=infer(hh,extent,state(hh,r['layout'],bp,models,m),F(*registry[bp][m]),m)
        for key in DIAGNOSTICS:
            m,variant=key.rsplit('_',1);geometries[key]=infer(hh,extent,state(hh,r['layout'],bp,models,m),F(*registry[bp][m]),m,variant)
        rr.update(prediction=local,ridge_center_um=centre,scores={m:[v.numerator,v.denominator] for m,v in ss.items()},geometries=geometries,oracle_us=[oracle_age(rr['true_xy'],body_um(extent),q) for q in ((-6000000,0),(6000000,0))]);rows.append(rr)
        for m,v in ss.items():scores[(r['episode_id'],m)]=max(scores[(r['episode_id'],m)],v)
        if (i+1)%250==0:print('test qualified',i+1,flush=True)
    lookup={r['id']:r for r in rows};rows=[lookup[r['id']] for r in records];assert sha(P/'calibration_frozen.json')==receipt_sha
    write(P/'qualification_sheng.json',dict(rows=rows,episodes=episodes,registry=registry,episode_scores={e['id']:{m:[scores[(e['id'],m)].numerator,scores[(e['id'],m)].denominator] for m in FAMILIES} for e in plan},catalog=catalog,basis=basis,calibration_receipt_sha256=receipt_sha,capture_manifest_sha256=sha(P/'capture/manifest.json'),model_freeze_sha256=sha(E/'freeze.json'),measurement_freeze_sha256=sha(E/'measurement_freeze.json'),scope=receipt['scope']));print('FINITE_FRESH_QUALIFICATION_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
