#!/usr/bin/env python3
"""Offline, same-information cross-check of already found pose witnesses."""
import argparse,hashlib,json,math
from pathlib import Path
from fractions import Fraction
import numpy as np
from audit import ROOT,rotation,contact,footprint_distance,face_module
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();audit=json.loads((a.results/'audit_sheng.json').read_bytes());sources={s['case']:s for s in json.loads((a.results/'replay/sources.json').read_bytes())};candidates=[];brackets=[];point_checks=0
    for case,source in sorted(sources.items()):
        with np.load(ROOT/source['source_cloud']) as z:
            raw=z['raw'];origin=z['origin'];world=np.c_[raw['x'],raw['y'],raw['z']].astype(float)@z['transform'][:3,:3].T+origin
        e=source['extent'];road=np.array(source['road_rotation']);anchor=np.array(source['anchor']);q=Fraction(source['threshold']['numerator'],source['threshold']['denominator']);radius=math.ceil(float(np.linalg.norm(e))*1e6)
        for qi in (0,1):
            query=np.array([-6. if qi==0 else 6.,0.]);poses=sorted({tuple(w['pose']) for w in audit['witness_bank'] if w['case']==case and w['query_index']==qi});bank=[]
            for pose0 in poses:
                pose=np.array(pose0);center=anchor+road@pose[:3];r=rotation(pose[3:]);scores=[face_module.reference(world[::stride],origin,center,r,e) for stride in (16,4,1)];point_checks+=sum(len(world[::s]) for s in (16,4,1));accepted=[max(Fraction(x['numerator'],x['denominator']) for x in scores[:i+1])<=q for i in range(3)];assert accepted[0] and all(not accepted[i+1] or accepted[i] for i in range(2));du=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);u=contact(du,0,radius)[1];distance=footprint_distance(pose,e,road,query);entry=dict(case=case,query_index=qi,pose=list(pose0),upper_us=u,scores=scores,accepted_by_stride={str(s):v for s,v in zip((16,4,1),accepted)},footprint_distance_m=round(distance,10),bounding_box_overlap=distance<=.75+1e-9);bank.append(entry);candidates.append(entry)
            for stride in (16,4,1):
                rr=[r for r in audit['rows'] if r['case']==case and r['query_index']==qi and r['stride']==stride];lower=max(r['lower_us'] for r in rr);original_upper=min(r['upper_us'] for r in rr);valid=[b for b in bank if b['accepted_by_stride'][str(stride)]];best=min(valid,key=lambda x:x['upper_us']) if valid else None;upper=min(original_upper,best['upper_us']) if best else original_upper;assert lower<=upper;brackets.append(dict(case=case,query_index=qi,stride=stride,lower_us=lower,upper_us=upper,gap_us=upper-lower,original_shared_upper_us=original_upper,candidate_count=len(bank),surviving_candidates=len(valid),best_pose=best['pose'] if best else None,chosen_bbox_overlap=best['bounding_box_overlap'] if best else None))
    summary={str(s):dict(candidates=len(candidates),surviving=sum(x['accepted_by_stride'][str(s)] for x in candidates),zero_witness_queries=sum(x['stride']==s and x['upper_us']==0 for x in brackets),queries=sum(x['stride']==s for x in brackets),max_upper_us=max(x['upper_us'] for x in brackets if x['stride']==s)) for s in (16,4,1)}
    out=dict(unique_candidates=len(candidates),full_reference_point_checks=point_checks,summary=summary,brackets=brackets,candidates=candidates,audit_sha256=hashlib.sha256((a.results/'audit_sheng.json').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Offline reuse of accepted poses from all schedulers, with each candidate independently rescored under every fixed nested budget. Same constructed score/disc posterior; not an online selector, physical counterfactual or proof that raw sensing is fundamentally insufficient.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
