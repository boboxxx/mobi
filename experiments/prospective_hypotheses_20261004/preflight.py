#!/usr/bin/env python3
"""Old development examples only; no fresh batch cloud or labels are read."""
from fractions import Fraction as F
from collections import Counter
from scores import load_models,predictions,current_scores
from inference import infer,state
from io_common import ROOT,E,P,read,write,sha
import argparse,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('fresh_hypotheses_audit',E/'audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=P/'preflight_old_development_local.json');a=ap.parse_args()
    models=load_models();old=read(ROOT/'results/prospective_shape_20261004/analysis_sheng.json');registry=read(ROOT/'results/calibrated_hypotheses_20261004/development_registry.json')['registry'];ridge=read(ROOT/'results/state_predictor_20261004/development_radii.json')['radii_um'];dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'];count=Counter();checks=0;statuses=Counter()
    for r in old['rows']:
        bp=r['blueprint']
        if count[bp]>=3:continue
        count[bp]+=1;rr=dict(r);extent=old['context']['catalog'][bp];pred,center=predictions(r['hulls_cm'],r['layout'],bp,models);ss=current_scores(r['hulls_cm'],extent,pred,center,r['true_xy']);independent=audit.scores(r['groups_cm'],r['hulls_cm'],extent,pred,center,r['true_xy'],dirs);assert ss==independent
        rr.update(prediction=pred,ridge_center_um=center,geometries={});qq=dict(joint=F(old['registry'][bp]['joint_slack_um']),ridge=F(ridge[bp]['ridge']),local_mean=F(*registry[bp]['local_mean']),local_modes=F(*registry[bp]['local_modes']))
        for key in ('joint','ridge','local_mean','local_modes','local_mean_plain','local_modes_plain','local_modes_clip'):
            m,variant=(key,'max') if key in qq else key.rsplit('_',1);actual=infer(r['hulls_cm'],extent,state(r['hulls_cm'],r['layout'],bp,models,m),qq[m],m,variant);rr['geometries'][key]=actual;expected=audit.geometry(rr,key,qq[m],extent,dirs);assert all(actual[k]==v for k,v in expected.items());checks+=1;statuses[key+'|'+actual['status']]+=1
    assert len(count)==6 and all(n==3 for n in count.values())
    write(a.out,dict(old_rows=sum(count.values()),independent_geometry_checks=checks,statuses=dict(statuses),fresh_data_read=False,scope='Archived already-observed development rows only; implementation preflight, no fresh qualification or new timing.'))
    print('OLD_DEVELOPMENT_IMPLEMENTATION_PREFLIGHT_PASS',checks,flush=True)
if __name__=='__main__':main()
