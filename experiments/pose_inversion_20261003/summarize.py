#!/usr/bin/env python3
import argparse,json,math,hashlib
from pathlib import Path
from fractions import Fraction
import numpy as np
from audit import ROOT,face_module,rotation,footprint_distance,contact
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;audit=json.loads((p/'audit_sheng.json').read_bytes());bank=json.loads((p/'witness_bank_sheng.json').read_bytes());summaries={}
    for variant in ('replay','refined'):
        rr=json.loads((p/variant/'rows.json').read_bytes());ww=[w for w in audit['witness_bank'] if w['variant']==variant];bybudget={}
        for stride in (16,4,1):
            r=[x for x in rr if x['stride']==stride];wire={x['wire_bytes'] for x in r};assert len(wire)==1;wire=wire.pop();bybudget[str(stride)]=dict(calls=len(r),positive_lower=sum(x['lower_us']>0 for x in r),zero_upper=sum(x['upper_us']==0 for x in r),median_receiver_ms=float(np.median([x['receiver_ns']/1e6 for x in r])),p95_receiver_ms=float(np.percentile([x['receiver_ns']/1e6 for x in r],95)),wire_bytes=wire,zero_compute_min_age_and_reserve_us=math.ceil(wire*8/20000000*1e6+20000+20000+200000),positive_usable=sum(x['usable_lower_us']>0 for x in r))
        summaries[variant]=dict(calls=len(rr),positive_lower=sum(x['lower_us']>0 for x in rr),zero_upper=sum(x['upper_us']==0 for x in rr),excluded_cells=sum(x['excluded_leaves'] for x in rr),zero_upper_with_bbox_overlap=sum(w['upper_us']==0 and w['bounding_box_footprint_overlaps_task'] for w in ww),zero_upper_without_bbox_overlap=sum(w['upper_us']==0 and not w['bounding_box_footprint_overlaps_task'] for w in ww),by_budget=bybudget)
    truth=[]
    for s in json.loads((p/'replay/sources.json').read_bytes()):
        r=next(r for r in json.loads((ROOT/s['source_record']).read_bytes()) if r.get('id')==s['source_id']);e=np.array(s['extent']);road=np.array(s['road_rotation']);center=np.array(r['center']);rotation0=rotation(np.deg2rad(r['actor_transform']['rotation']));pose=np.r_[road.T@(center-s['anchor']),np.deg2rad(r['actor_transform']['rotation'])];pose[4]%=2*math.pi;cal=json.loads((ROOT/s['calibration_analysis']).read_bytes());q=Fraction(s['threshold']['numerator'],s['threshold']['denominator'])
        with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];points=np.c_[raw['x'],raw['y'],raw['z']].astype(float)@z['transform'][:3,:3].T+z['origin'];origin=z['origin']
        scores=[]
        for stride in (16,4,1):
            score=face_module.reference(points[::stride],origin,center,rotation0,e);previous=next(x['truth'] for x in cal['rows'] if x['id']==s['source_id'] and x['stride']==stride);assert score==previous;scores.append(score)
        accepted=max(Fraction(x['numerator'],x['denominator']) for x in scores)<=q
        for qi,query in enumerate([[-6.,0.],[6.,0.]]):
            distance=footprint_distance(pose,e,road,np.array(query));delta=(pose[:2]-query)*1e6;du=math.floor(float(np.linalg.norm(delta))-1e-7);oracle=contact(max(0,du),0,math.ceil(float(np.linalg.norm(e))*1e6))[0];truth.append(dict(case=s['case'],query_index=qi,true_pose_retained_by_all_budgets=accepted,true_bbox_footprint_distance_m=round(distance,10),true_bbox_clear=distance>.75,oracle_pose_disc_lower_us=oracle))
    out=dict(variants=summaries,witness_bank=bank['summary'],unique_bank_candidates=bank['unique_candidates'],bank_point_checks=bank['full_reference_point_checks'],tree_nodes_checked=audit['tree_nodes'],packet_checks=audit['packet_checks'],declared_pose_domain_violations=sum(not x['inside_declared_domain'] for x in audit['truth_domain']),truth_diagnostics=truth,truth_pose_excluded_source_cases=len({x['case'] for x in truth if not x['true_pose_retained_by_all_budgets']}),true_bbox_clear_queries=sum(x['true_bbox_clear'] for x in truth),oracle_pose_positive_queries=sum(x['oracle_pose_disc_lower_us']>0 for x in truth),oracle_pose_lower_range_us=[min(x['oracle_pose_disc_lower_us'] for x in truth),max(x['oracle_pose_disc_lower_us'] for x in truth)],audit_sha256=hashlib.sha256((p/'audit_sheng.json').read_bytes()).hexdigest(),witness_bank_sha256=hashlib.sha256((p/'witness_bank_sheng.json').read_bytes()).hexdigest(),scope='Retrospective descriptive results, not independent statistical trials. Oracle poses and bbox overlaps are audit-only diagnostics. No physical-safety, optimal raw-information lifetime or new algorithmic superiority claim.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('truth_diagnostics','variants','scope')},indent=2))
if __name__=='__main__':main()
