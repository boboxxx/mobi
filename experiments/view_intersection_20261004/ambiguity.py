#!/usr/bin/env python3
"""Post-result abstract-set collision witnesses, not raw-compatible worlds."""
import argparse,hashlib,json
from pathlib import Path
from decimal import Decimal,localcontext
from audit import certificate
PS=10**12
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=read(a.results/'analysis_sheng.json');audit=read(a.results/'audit_sheng.json');assert audit['analysis_sha256']==sha(a.results/'analysis_sheng.json');parent=read(a.parent/'analysis_sheng.json');original={r['id']:r for r in parent['rows']};bps=list(parent['registry']);records=[];counts={bp:dict(bounded_queries=0,model_current_contact_possible=0,actual_current_free_but_model_contact_possible=0,covered_actual_free_but_model_contact_possible=0) for bp in bps}
    for pair in d['pairs'].values():
        if pair['geometry']['status']!='bounded':continue
        first,second=[original[s] for s in pair['source_ids']];left=[[v*10000 for v in c] for c in pair['left_cm']];right=[[v*10000 for v in c] for c in pair['right_cm']]
        for index,z in enumerate(pair['geometry']['queries']):
            c=counts[pair['blueprint']];c['bounded_queries']+=1;contact_radius=pair['body_um']+750000
            if z['distance']['upper_um']>contact_radius:continue
            proof=min((x for x in z['distance']['proofs'] if x['kind']!='disjoint'),key=lambda x:x['upper_um']);certificate(proof,left,right,z['query'],pair['radius_um']);point=proof['point']
            assert sum((point[k]-z['query'][k]*PS)**2 for k in range(2)) <= (contact_radius*PS)**2
            with localcontext() as ctx:
                ctx.prec=80
                truth=[Decimal(str(v))*1000000 for v in first['true_xy']]
                free=sum((truth[k]-z['query'][k])**2 for k in range(2))>contact_radius**2
            covered=first['covered'] and second['covered'];c['model_current_contact_possible']+=1;c['actual_current_free_but_model_contact_possible']+=free;c['covered_actual_free_but_model_contact_possible']+=covered and free
            records.append(dict(pair_id=pair['id'],blueprint=pair['blueprint'],query_index=index,source_us=pair['source_us'],query_um=z['query'],body_and_query_um=contact_radius,radius_um=pair['radius_um'],actual_current_free=free,both_views_covered=covered,abstract_supported_contact_witness=proof,source_ids=pair['source_ids']))
    result=dict(classes=[dict(blueprint=bp,**counts[bp]) for bp in bps],witnesses=records,source_sha256=sha(Path(__file__)),certificate_auditor_sha256=sha(Path(__file__).with_name('audit.py')),analysis_sha256=sha(a.results/'analysis_sheng.json'),audit_sha256=sha(a.results/'audit_sheng.json'),parent_analysis_sha256=sha(a.parent/'analysis_sheng.json'),scope='Exact rational feasible supported-center collision witnesses inside the two calibrated unions, while actual source-center truth is used only for post-result diagnosis. These states are NOT proven compatible with original XYZ/rays, physical meshes or motion; no raw-information impossibility or new policy/risk fit.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(result['classes']))
if __name__=='__main__':main()
