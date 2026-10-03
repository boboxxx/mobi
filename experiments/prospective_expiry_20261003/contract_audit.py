#!/usr/bin/env python3
"""Audit known extent identity, actual XY corner support and transform precision."""
import argparse,hashlib,json,math
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'analysis_sheng.json').read_bytes());catalog=d['contract_body']['catalog'];eps=d['episodes'];records=d['rows'];out=[]
    for bp,ext in catalog.items():
        ee=[e for e in eps if e['episode']['blueprint']==bp and e['status']=='captured'];rr=[r for r in records if r['blueprint']==bp];radius=math.ceil(math.sqrt(sum(v*v for v in ext))*1e6)/1e6;corner_count=outside=0;excess=precision=0.;extent_mismatch=sum(r['bounding_box']['extent']!=ext for r in rr)
        for ep in ee:
            extent_mismatch+=ep['bounding_box']['extent']!=ext;loc=ep['bounding_box']['location']
            for t in ep['trajectory']:
                mat=t['actor_transform']['matrix'];computed=[sum(mat[i][j]*loc[j] for j in range(3))+mat[i][3] for i in range(3)];precision=max(precision,math.sqrt(sum((x-y)**2 for x,y in zip(computed,t['center']))))
                for v in t['world_vertices']:
                    corner_count+=1;distance=math.hypot(v[0]-t['center'][0],v[1]-t['center'][1]);outside+=distance>radius;excess=max(excess,distance-radius)
        out.append(dict(blueprint=bp,captured_episodes=len(ee),stored_source_records=len(rr),declared_extent=ext,body_um=math.ceil(radius*1e6),extent_identity_mismatches=extent_mismatch,xy_corner_checks=corner_count,xy_outside_corners=outside,max_positive_xy_corner_excess_um_ceil=math.ceil(max(0.,excess)*1e6),max_center_matrix_API_discrepancy_um_ceil=math.ceil(precision*1e6)))
    result=dict(summary=out,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Exact saved nominal extent identity and all saved API bbox vertices against the XY body disc. Separately reports API-versus-float64-transform center differences with outward integer micrometer rounding. Does not prove unseen physical mesh containment or inter-snapshot motion/geometry.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
