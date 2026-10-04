#!/usr/bin/env python3
"""Post-result conditional-model contact witnesses; no physical-world claim."""
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'analysis_sheng.json').read_bytes());audit=json.loads((p/'audit_sheng.json').read_bytes());base=ROOT/'results/prospective_expiry_20261003';prior=json.loads((base/'analysis_sheng.json').read_bytes());parent={r['id']:r for r in prior['rows']};c={r['id']:r for r in audit['frame_checks']};records=[]
 for r in d['rows']:
  if r['geometry']['status']!='bounded' or not c[r['id']]['covered']:continue
  for qid,q in enumerate(r['geometry']['queries']):
   if c[r['id']]['oracle_us'][qid][0]<220000 or q['lower_us']>0:continue
   for gid,proof in enumerate(q['proofs']):
    if proof['kind'] in ('dual','inside'):point=proof['point'];den=1000000
    elif proof['kind']=='singleton':point=proof['point_num'];den=proof['point_den']
    else:continue
    if sum((point[k]-q['query'][k]*den)**2 for k in (0,1))>(den*(r['body_um']+750000))**2:continue
    vertices=r['geometry']['hulls_cm'][gid];assert all(sum((point[k]-v[k]*10000*den)**2 for k in (0,1))<=(r['radius_um']*den)**2 for v in vertices)
    old=parent[r['id']];records.append(dict(id=r['id'],blueprint=r['blueprint'],episode_id=r['episode_id'],query=q['query'],oracle_us=c[r['id']]['oracle_us'][qid],model_expiry_us=[q['lower_us'],q['upper_us']],component=gid,candidate_center_num_um=point,candidate_center_den=den,body_um=r['body_um'],support_radius_um=r['radius_um'],hull_cm=vertices,true_xy=old['true_xy'],cloud=str((base/'capture'/old['cloud_file']).relative_to(ROOT)),cloud_sha256=old['cloud_sha256'],scope='Exact contact witness inside abstract body-support intersection; not a proven all-ray/mesh-compatible physical state'));break
 out=dict(witnesses=records,counts_by_class={bp:sum(r['blueprint']==bp for r in records) for bp in d['context']['catalog']},source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),scope='Post-result raw-linked diagnosis. The new geometric solver is near optimal for this model but these abstract states explain some remaining conservative refusals. No new validity authority, score fitting, threshold change or physical identifiability proof.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('model contact witnesses',len(records),out['counts_by_class'])
if __name__=='__main__':main()
