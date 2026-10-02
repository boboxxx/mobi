#!/usr/bin/env python3
"""Independent64-corner ray-plane bound; no projection/selection call."""
import argparse,gzip,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
import analyze as reference
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();basepath=a.results/'study/analysis.json';base=json.loads(basepath.read_bytes());s=json.loads((a.results/'extra_ray_study/analysis.json').read_bytes());assert s['sphere_study_sha256']==sha(basepath) and len(s['rows'])==36
    for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h
    summaries=[]
    for row in s['rows']:
        original=next(r for r in base['rows'] if (r['run'],r['index'],r['klass'])==(row['run'],row['index'],row['klass']));assert row['witness']==original['witness'] and row['source_path']==original['received_paths'][-1]
        for name in ['source','cloud','record']:assert sha(ROOT/row[name+'_path'])==row[name+'_sha256']
        fact=a.results/'extra_ray_study'/row['fact'];assert sha(fact)==row['fact_sha256'] and len(fact.read_bytes())==row['bytes'];raw=json.loads(fact.read_bytes());p=raw['payload'];assert hashlib.sha256(reference.body.canonical(p)).hexdigest()==raw['sha256'] and len(p['rays'])==len(p['origins'])==1
        old=json.loads((ROOT/row['source_path']).read_bytes())['payload']
        for field in ['version','scope','contract','profiles','reference_us','sequence']:assert p[field]==old[field]
        record=json.loads(gzip.decompress((ROOT/row['record_path']).read_bytes()));d=next(d for d in record['decisions'] if d['id']=='drive_%03d'%row['index']);assert p['reference_us']==row['ref_us']==math.ceil(d['stamp']*1e6)
        with np.load(ROOT/row['cloud_path']) as z:xyz=z['xyz'];origin=np.broadcast_to(z['origin'],xyz.shape)[row['cloud_ray_index']]
        assert len(xyz)==row['full_scan_rays'];point=xyz[row['cloud_ray_index']];oq=np.rint(origin/.001).astype(np.int64);pq=np.rint(point/.001).astype(np.int64);ray=[0]+pq.tolist()+[math.floor(d['stamp']*1e6)];assert p['origins']==[oq.tolist()] and p['rays']==[ray]
        selected={tuple(old['origins'][r[0]])+tuple(r[1:]) for r in old['rays']};assert tuple(oq)+tuple(ray[1:]) not in selected and len(old['rays'])==row['selected_rays']
        o=oq*.001;point=pq*.001;error=p['contract'];pe=error['point_error']+.0005;oe=error['origin_error']+.0005;plane=p['scope']['plane_z'];assert o[2]-oe>plane+1e-9 and point[2]+pe<plane-1e-9
        crossings=[]
        corners=list(itertools.product([-1,1],repeat=3))
        for a0 in corners:
            oo=o+np.array(a0)*oe
            for b0 in corners:
                pp=point+np.array(b0)*pe;t=(oo[2]-plane)/(oo[2]-pp[2]);assert 0<t<1;crossings.append((1-t)*oo[:2]+t*pp[:2])
        crossings=np.array(crossings);lo=crossings.min(axis=0)-error['query_error'];hi=crossings.max(axis=0)+error['query_error']
        # Candidate position at THIS observed timestamp, after last speed sample.
        age=(row['ref_us']-ray[4])/1e6;w=row['witness'];center=np.asarray(w['center_reference'])+np.asarray(w['outward_direction'])*(5*age+1.5*age*age)
        furthest=math.hypot(max(abs(lo[0]-center[0]),abs(hi[0]-center[0])),max(abs(lo[1]-center[1]),abs(hi[1]-center[1])));core=p['profiles'][row['klass']]['r_min'];margin=core-furthest-1e-8;assert margin>0
        assert row['selection_ms']>=0 and math.isfinite(row['selection_ms']);summaries.append(dict(run=row['run'],index=row['index'],klass=row['klass'],bytes=row['bytes'],independent_core_exclusion_margin_m=round(margin,6),box_corner_pairs=64))
    out=dict(cases=36,refuted=36,box_corner_pairs=2304,summaries=summaries,analyzer_sha256=sha(Path(__file__)),scope='Independent actual-cloud, untransmitted-ray and64-corner refutation of36 original candidates; changes received information; not a longer TTL or action certificate.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['summaries','scope']}))
if __name__=='__main__':main()
