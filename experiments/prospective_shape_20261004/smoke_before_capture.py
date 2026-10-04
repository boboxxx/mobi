#!/usr/bin/env python3
"""Development-only end-to-end schema/model/wire preflight, not fresh evidence."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent;sys.path.insert(0,str(E))
from evaluate import ROOT,record,pack,pack_raw,unpack,decode_raw,infer,read,DIRECTIONS,POLICIES
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();pp=ROOT/'results/prospective_expiry_20261003';prior=read(pp/'analysis_sheng.json');pose=read(ROOT/'results/pose_support_20261004/analysis_sheng.json');lookup={r['id']:r for r in read(pp/'capture/record.json')};catalog=read(E/'catalog.json');basis=prior['contract_body']['basis'];bg=read(ROOT/'results/background_frontend_20261004/background.json');selected=[]
 for bp in catalog:
  pool=[r for r in pose['rows'] if r['blueprint']==bp];selected.extend([max(pool,key=lambda r:r['joint_score_um']),next(r for r in pool if r['layout']==1)])
 rows=[];matrices={};inputs={}
 for r in selected:rows.append(record(lookup[r['id']],pp,catalog,basis,bg,inputs,matrices))
 slacks={bp:max(v['joint_score_um'] for v in rows if v['blueprint']==bp) for bp in catalog};contract=hashlib.sha256(b'development-only-fresh-schema-smoke').hexdigest();calibration=hashlib.sha256(json.dumps(slacks,sort_keys=True).encode()).hexdigest();ctx=dict(catalog=catalog,basis=basis,background=bg,slacks_um=slacks,raw_transport=dict(contract=contract,calibration=calibration,transforms=matrices),directions=DIRECTIONS,tilt_operator_norm_upper=[87267,1000000],yaw_cell_distance_factor=[8730,1000000]);count=0
 for r in rows:
  with np.load(pp/'capture'/r['cloud_file']) as z:raw=z['raw'];T=z['transform'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4')
  ci=list(catalog).index(r['blueprint'])
  for policy in POLICIES:
   if policy=='joint_raw':wire=pack_raw(xyz,T,ci,r['frame'],r['timestamp'],contract,calibration);decoded,hh=decode_raw(wire,ctx);assert hh==r['hulls_cm']
   else:wire=pack('hull',r['hulls_cm'],ci,r['layout'],r['frame'],r['source_us'],contract,calibration);decoded=unpack(wire,policy,ctx,contract,calibration)
   expected=infer(r['hulls_cm'],catalog[r['blueprint']],slacks[r['blueprint']],policy);assert all(decoded[k]==v for k,v in expected.items()) and decoded['source_us']==r['source_us'] and decoded['frame']==r['frame'] and decoded['class_index']==ci and decoded['layout']==r['layout'];count+=1
 out=dict(development_row_ids=[r['id'] for r in rows],wire_checks=count,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_hashes=inputs,scope='Pre-capture old-data smoke only; no new observations, risk fit, policy fees or qualification. Exercises newly written record/schema with frozen inherited runtime and strong RAW hull reduction.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('SMOKE_OK',len(rows),count,flush=True)
if __name__=='__main__':main()
