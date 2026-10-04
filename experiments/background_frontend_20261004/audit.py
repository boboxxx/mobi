#!/usr/bin/env python3
"""Independent sorted-voxel/raster extraction audit; never imports producer/model."""
import argparse,hashlib,importlib.util,json,math,zlib
from collections import Counter
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_raster',ROOT/'experiments/positive_state_20261003/audit.py');raster=importlib.util.module_from_spec(spec);spec.loader.exec_module(raster)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def local_points(r,base):
    with np.load(base/'capture'/r['cloud_file']) as z:
        raw=z['raw'];p=np.c_[raw['x'],raw['y'],raw['z']].astype(float);T=z['transform']
    # Fixed saved transform+basis, checked bytewise against the parent analyses.
    local=(p@T[:3,:3].T+T[:3,3]-r['anchor'])@np.asarray(r['road'])
    return local,raw

def codes(p):
    valid=(np.abs(p[:,0])<=12)&(np.abs(p[:,1])<=8)&(p[:,2]>.3)&(p[:,2]<3)
    g=np.floor(p[valid]*10).astype(np.int64)
    # Independent 3D tuple representation; serialization is checked separately.
    out=np.empty(len(p),dtype=object);out[:]=None
    for i,k in zip(np.nonzero(valid)[0],g):out[i]=tuple(int(v) for v in k)
    return out

def inside(cm,q,xy):
    if not len(cm):return True
    with localcontext() as ctx:
        ctx.prec=80;true=[Decimal.from_float(float(v))*1000000 for v in xy]
        return any(sum((Decimal(int(c[j])*10000)-true[j])**2 for j in (0,1))<=q*q for c in cm)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');bg=read(p/'background.json')
    for mapping in (read(E/'freeze.json')['sources'],d['source_hashes'],d['input_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    for key,study in [('parent_analysis_sha256','prospective_expiry_20261003'),('fit_parent_analysis_sha256','causal_state_20261003')]:assert d[key]==sha(ROOT/'results'/study/'analysis_sheng.json')
    assert d['background_sha256']==sha(p/'background.json') and d['setup_wire_sha256']==sha(p/'background.bin') and d['setup_wire_bytes']==(p/'background.bin').stat().st_size
    blob=zlib.decompress((p/'background.bin').read_bytes());assert hashlib.sha256(blob[:-32]).digest()==blob[-32:] and json.loads(blob[:-32])==bg
    prior=ROOT/'results/causal_state_20261003';current=ROOT/'results/prospective_expiry_20261003';old=read(prior/'analysis_sheng.json');parent=read(current/'analysis_sheng.json');fit=[r for r in old['rows'] if r['split']=='calibration' and r['step']==0];assert bg['fit_rows']==[r['id'] for r in fit] and bg['basis']==parent['contract_body']['basis']==old['contract_body']['basis'];cc={0:Counter(),1:Counter()};ns={0:0,1:0}
    for r in fit:
        local,raw=local_points(r,prior);unique={x for x in codes(local) if x is not None};cc[r['layout']].update(unique);ns[r['layout']]+=1
    static={}
    for k in (0,1):
        threshold=math.ceil(.9*ns[k]);static[k]={c for c,n in cc[k].items() if n>=threshold};m=bg['layouts'][str(k)];expected=sorted((c[0]+120)*161*27+(c[1]+80)*27+c[2]-3 for c in static[k]);assert m==dict(fit_scans=ns[k],threshold=threshold,codes=expected)
    assert bg['fit_input_hashes']=={str((prior/'capture'/r['cloud_file']).relative_to(ROOT)):r['cloud_sha256'] for r in fit}
    assert [r['id'] for r in d['rows']]==[r['id'] for r in parent['rows']];checks=[];score_by_episode={};calculated=[]
    for r,saved in zip(parent['rows'],d['rows']):
        local,raw=local_points(r,current);assert saved['true_xy']==r['true_xy'];ext=d['catalog'][r['blueprint']];variants=[]
        for shift,v in zip((0.,.001,.01),saved['variants']):
            assert shift==v['shift_m'];shifted=local+shift;keys=codes(shifted);removed=np.array([k is not None and k in static[r['layout']] for k in keys]);remaining=shifted[~removed];rr=np.empty(len(remaining),dtype=[('x','<f8'),('y','<f8'),('z','<f8')]);rr['x'],rr['y'],rr['z']=remaining.T;c,meta=raster.proposals(rr,np.eye(4),np.zeros(3),0.,ext);cm=np.rint(c*100).astype(np.int32)
            # Raster component order differs; compare sorted centers and cm independently.
            expected=np.asarray(v['centers']).reshape(-1,2);np.testing.assert_allclose(sorted(map(tuple,c)),sorted(map(tuple,expected)),rtol=0,atol=1e-10);assert sorted(map(tuple,cm))==sorted(map(tuple,v['centers_cm']))
            assert dict(**meta,background_removed=int(removed.sum()))==v['metadata'] and v['available']==bool(len(c))
            residual=min([math.hypot(*(x-r['true_xy'])) for x in c]) if len(c) else 0.;assert abs(residual-v['residual_m'])<1e-10
            q=d['registry'][r['blueprint']]['radius_um'];covered=inside(cm,q,r['true_xy']);assert covered==v['covered'];h=[list(raster.horizon(cm,q,ext,x)) for x in (-6000000,6000000)] if len(c) else [[0,500000],[0,500000]];assert h==v['bounds']
            target=raw['id']==r['actor_id'];assert int(target.sum())==v['target_returns'] and int(np.sum(target&removed))==v['target_returns_removed']
            if shift==0:
                assert len(v['samples_s'])==3 and all(s>=0 for s in v['samples_s']) and v['source_us']==math.ceil(max(v['samples_s'])*1e6);score_by_episode[r['episode_id']]=max(score_by_episode.get(r['episode_id'],0.),residual)
            else:assert v['samples_s']==[] and v['source_us'] is None
            variants.append(dict(shift_m=shift,available=bool(len(c)),covered=covered,bounds=h,target_returns_removed=int(np.sum(target&removed)),target_returns=int(target.sum()),proposals_changed=sorted(map(tuple,cm))!=sorted(map(tuple,saved['variants'][0]['centers_cm']))))
        checks.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],variants=variants))
        if len(checks)%500==0:print('audited',len(checks),flush=True)
    for e in parent['episodes']:score_by_episode.setdefault(e['episode']['id'],0.)
    assert all(abs(score_by_episode[k]-v)<1e-10 for k,v in d['calibration_scores'].items())
    for bp in d['catalog']:
        ss=[score_by_episode[e['episode']['id']] for e in parent['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ss)==95;assert math.ceil(max(ss)*1e6+1e-7)+8000==d['registry'][bp]['radius_um']
    out=dict(fit_scans=ns,static_voxels={k:len(v) for k,v in static.items()},frame_checks=checks,source_sha256=sha(Path(__file__)),parent_raster_auditor_sha256=sha(ROOT/'experiments/positive_state_20261003/audit.py'),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent voxel tuple counts, raster labels, all raw XYZ, Decimal coverage and integer age endpoints. Development-only, no new prospective risk or paid action policy.')
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('complete',len(checks),flush=True)
if __name__=='__main__':main()
