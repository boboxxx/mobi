#!/usr/bin/env python3
"""Frozen finite model-adequacy diagnostic; no new risk guarantee or action gate."""
import argparse,hashlib,importlib.util,json,math,sys,time,zlib
from pathlib import Path
import numpy as np
from model import voxel_codes,extract
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('diagnostic_disc_age',ROOT/'experiments/shape_evidence_20261002/lifetime.py')
life=importlib.util.module_from_spec(spec);sys.modules[spec.name]=life;spec.loader.exec_module(life)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_row(r,base):
    path=base/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
    with np.load(path) as z:
        raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float);matrix=z['transform'].copy()
    return xyz,matrix,raw,path

def horizons(cm,q,ext):
    if not len(cm):return [[0,500000],[0,500000]]
    body=math.ceil(float(np.linalg.norm(ext))*1e6)
    ss=[life.State(int(c[0])*10000,int(c[1])*10000,q+body,5000000,3000000) for c in cm]
    out=[]
    for x in (-6000000,6000000):
        a=life.expiry(ss,(x,0),750000,500000,complete_support=True);h=a['safe_through_us'];out.append([h,h if a['reason']=='unsafe_at_observation' or a['capped'] else h+1])
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results
    assert not (p/'analysis_sheng.json').exists();p.mkdir(parents=True,exist_ok=True)
    prior=ROOT/'results/causal_state_20261003';current=ROOT/'results/prospective_expiry_20261003'
    old=json.loads((prior/'analysis_sheng.json').read_bytes());d=json.loads((current/'analysis_sheng.json').read_bytes());assert old['contract_body']['basis']==d['contract_body']['basis']
    fit_rows=[r for r in old['rows'] if r['split']=='calibration' and r['step']==0];counts={0:{},1:{}};ns={0:0,1:0};inputs={};start=time.perf_counter()
    for r in fit_rows:
        xyz,T,raw,path=load_row(r,prior);inputs[str(path.relative_to(ROOT))]=sha(path)
        local=(xyz@T[:3,:3].T+T[:3,3]-r['anchor'])@np.array(r['road']);codes=set(int(c) for c in voxel_codes(local) if c>=0);layout=r['layout'];ns[layout]+=1
        for code in codes:counts[layout][code]=counts[layout].get(code,0)+1
    maps={str(k):dict(fit_scans=ns[k],threshold=(9*ns[k]+9)//10,codes=sorted(c for c,n in counts[k].items() if 10*n>=9*ns[k])) for k in (0,1)}
    background=dict(layouts=maps,fit_rows=[r['id'] for r in fit_rows],basis=d['contract_body']['basis'],voxel_m=.1,minimum_fraction=.9,fit_input_hashes=inputs.copy(),fit_elapsed_s=time.perf_counter()-start)
    # Transfer format includes provenance, frame counts, coordinate basis and checksum.
    payload=json.dumps(background,sort_keys=True,separators=(',',':')).encode();wire=zlib.compress(payload+hashlib.sha256(payload).digest(),6);(p/'background.bin').write_bytes(wire);(p/'background.json').write_text(json.dumps(background,separators=(',',':'))+'\n')
    rows=[];catalog=d['contract_body']['catalog']
    for r in d['rows']:
        xyz,T,raw,path=load_row(r,current);inputs[str(path.relative_to(ROOT))]=sha(path);ext=catalog[r['blueprint']];static=maps[str(r['layout'])]['codes'];variants=[]
        for shift in (0.,.001,.01):
            samples=[]
            for j in range(3 if shift==0 else 1):
                t=time.perf_counter();c,meta=extract(xyz,T,np.asarray(r['anchor']),np.asarray(r['road']),ext,static,shift);cm=np.rint(c*100).astype(np.int32);elapsed=time.perf_counter()-t
                if shift==0:samples.append(elapsed)
            error=float(np.min(np.linalg.norm(c-r['true_xy'],axis=1))) if len(c) else 0.
            local=(xyz@T[:3,:3].T+T[:3,3]-r['anchor'])@np.asarray(r['road'])+shift;codes=voxel_codes(local);removed=(codes>=0)&np.isin(codes,static)
            # IDs are accessed only here, after the XYZ-only extraction, for diagnosis.
            target=raw['id']==r['actor_id'];variants.append(dict(shift_m=shift,centers=c.tolist(),centers_cm=cm.tolist(),metadata=meta,residual_m=error,available=bool(len(c)),target_returns_removed=int(np.sum(target&removed)),target_returns=int(target.sum()),samples_s=samples,source_us=math.ceil(max(samples)*1e6) if samples else None))
        rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],step=r['step'],layout=r['layout'],old_residual_m=r['residual_m'],old_available=r['available'],true_xy=r['true_xy'],variants=variants))
        if len(rows)%200==0:print('processed',len(rows),flush=True)
    scores={};registry={}
    for e in d['episodes']:
        ep=e['episode'];scores[ep['id']]=max([r['variants'][0]['residual_m'] for r in rows if r['episode_id']==ep['id']]+[0.])
    for bp in catalog:
        ss=[scores[e['episode']['id']] for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ss)==95
        registry[bp]=dict(radius_um=math.ceil(max(ss)*1e6+1e-7)+8000,calibration_n=95,rank=95,scope='Descriptive development radius, not new prospective risk qualification')
    for r in rows:
        for v in r['variants']:
            cm=np.array(v['centers_cm'],dtype=np.int32).reshape(-1,2);q=registry[r['blueprint']]['radius_um'];dist=float(np.min(np.linalg.norm(cm/100.-r['true_xy'],axis=1))) if len(cm) else 0.;v['covered']=not len(cm) or dist*1e6<=q;v['bounds']=horizons(cm,q,catalog[r['blueprint']])
    deps=[E/n for n in ('evaluate.py','model.py','PROTOCOL.md')]+[ROOT/'experiments/positive_state_20261003/model.py',ROOT/'experiments/shape_evidence_20261002/lifetime.py']
    result=dict(rows=rows,episodes=d['episodes'],registry=registry,calibration_scores=scores,old_registry=d['registry'],catalog=catalog,input_hashes=inputs,source_hashes={str(f.relative_to(ROOT)):sha(f) for f in deps},parent_analysis_sha256=sha(current/'analysis_sheng.json'),fit_parent_analysis_sha256=sha(prior/'analysis_sheng.json'),background_sha256=sha(p/'background.json'),setup_wire_sha256=sha(p/'background.bin'),setup_wire_bytes=len(wire),setup_scope='Full compressed fit provenance+basis+voxel reference; not free or excluded setup',scope='Frozen finite post-result background model adequacy diagnostic. Descriptive development radii only; no new holdout, prospective risk guarantee, messages, paid action policy, live link/ego or novelty.')
    (p/'analysis_sheng.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print('complete',len(rows),flush=True)
if __name__=='__main__':main()
