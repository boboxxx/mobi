#!/usr/bin/env python3
"""Independent calibration, then policy certification, then test: enforced processing order."""
import bootstrap
import argparse,hashlib
from collections import defaultdict
from fractions import Fraction as F
from fresh_io import ROOT,E,P,read,write,sha,canon,freeze_check,observed_record
from scores import FAMILIES,load_models,predictions,current_scores
from fresh_inference import PRIMARY,component,state,infer,threshold
from integer_state import oracle_age,body_um
COMPONENTS=('supported_mean','supported_modes','fallback_um');ALL=FAMILIES+COMPONENTS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',choices=('calibration','certification','test'),required=True);a=ap.parse_args();split=a.split
    freeze_check();assert (P/'capture_terminal.txt').read_text()=='FRESH_COMPONENT_CAPTURE_COMPLETE\n' and read(P/'server_stopped.json')['stopped']
    output=P/('calibration_frozen.json' if split=='calibration' else 'qualification_'+split+'_sheng.json');assert not output.exists()
    plan=read(E/'plan.json');records=read(P/'capture/record.json');episodes=read(P/'capture/episodes.json');assert len(plan)==2520 and [e['episode'] for e in episodes]==plan
    catalog=read(E/'catalog.json');bg=read(ROOT/'results/background_frontend_20261004/background.json');models=load_models();events=defaultdict(lambda:F(0));rows=[];inputs={};receipt=None
    if split!='calibration':
        receipt=read(P/'calibration_frozen.json');receipt_sha=sha(P/'calibration_frozen.json');registry=receipt['registry'];assert receipt['calibration_n_per_class']==260
        if split=='test':assert read(P/'policy_frozen.json')['certification_complete'];policy_sha=sha(P/'policy_frozen.json')
        write(P/('order_'+split+'.json'),dict(split=split,calibration_receipt_sha256=receipt_sha,policy_receipt_sha256=policy_sha if split=='test' else None,stage_clouds_read=0,receipt_written_before_stage_processing=True))
    for i,r in enumerate(v for v in records if v['split']==split):
        rr=observed_record(r,catalog,bg['basis'],bg);bp=r['blueprint'];hh=rr['hulls_cm'];ext=catalog[bp];pred,centre=predictions(hh,r['layout'],bp,models);ss=current_scores(hh,ext,pred,centre,rr['true_xy']);ss.update(component.conformity(hh,ext,pred,rr['true_xy']));rr.update(prediction=pred,ridge_center_um=centre,scores={m:[v.numerator,v.denominator] for m,v in ss.items()})
        if split!='calibration':
            rr.update(geometries={m:infer(hh,ext,state(hh,r['layout'],bp,models,m),threshold(registry,bp,m),m) for m in PRIMARY},oracle_us=[oracle_age(rr['true_xy'],body_um(ext),q) for q in ((-6000000,0),(6000000,0))])
        rows.append(rr);inputs[str((P/'capture'/r['cloud_file']).relative_to(ROOT))]=r['cloud_sha256']
        for m,v in ss.items():events[r['episode_id'],m]=max(events[r['episode_id'],m],v)
        if (i+1)%500==0:print(split,'scored',i+1,flush=True)
    episode_scores={e['id']:{m:[events[e['id'],m].numerator,events[e['id'],m].denominator] for m in ALL} for e in plan if e['split']==split}
    if split=='calibration':
        registry={}
        for bp in catalog:
            eps=[e for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(eps)==260;registry[bp]={m:[max(events[e['id'],m] for e in eps).numerator,max(events[e['id'],m] for e in eps).denominator] for m in ALL}
        bound=18*F(39,40)**260+24*F(19,20)**260;assert bound<=F(1,40)
        write(output,dict(registry=registry,calibration_sha256=hashlib.sha256(canon(registry)).hexdigest(),calibration_episode_scores=episode_scores,input_hashes=inputs,model_freeze_sha256=sha(E/'freeze.json'),measurement_freeze_sha256=sha(E/'freeze.json'),calibration_n_per_class=260,component_exclusion_target=[1,40],baseline_exclusion_target=[1,20],confidence_error_bound=[bound.numerator,bound.denominator],rows=rows,catalog=catalog,basis=bg['basis'],scope='Fixed-class integer-grid IID planned whole episodes; 18 component and24 baseline calibration events. Marginal family union risk5%, not conditional authorization risk.'))
    else:
        write(output,dict(rows=rows,episodes=[e for e in episodes if e['episode']['split']==split],registry=registry,episode_scores=episode_scores,catalog=catalog,basis=bg['basis'],calibration_receipt_sha256=receipt_sha,capture_manifest_sha256=sha(P/'capture/manifest.json'),model_freeze_sha256=sha(E/'freeze.json'),measurement_freeze_sha256=sha(E/'freeze.json'),scope=receipt['scope']))
        assert sha(P/'calibration_frozen.json')==receipt_sha
    print('FINITE_COMPONENT_'+split.upper()+'_QUALIFICATION_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
