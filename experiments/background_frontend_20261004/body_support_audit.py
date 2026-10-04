#!/usr/bin/env python3
"""Independent BFS all-point support reconstruction and Decimal score auditing."""
import argparse,hashlib,json,math
from decimal import Decimal,localcontext,ROUND_CEILING
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canonical(g):return tuple(sorted(tuple(map(int,p)) for p in g))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--body',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;body=read(a.body);d=read(p/'analysis_sheng.json');assert body['analysis_sha256']==sha(p/'analysis_sheng.json') and body['background_sha256']==sha(p/'background.json') and body['source_sha256']==sha(E/'body_support.py');bg=read(p/'background.json');base=ROOT/'results/prospective_expiry_20261003';parent=read(base/'analysis_sheng.json');checks=[];ep_scores={};group_checks=point_checks=0
    assert [r['id'] for r in body['rows']]==[r['id'] for r in parent['rows']]
    for source,saved,front in zip(parent['rows'],body['rows'],d['rows']):
        path=base/'capture'/source['cloud_file'];assert sha(path)==source['cloud_sha256']
        with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float);T=z['transform']
        local=(xyz@T[:3,:3].T+T[:3,3]-source['anchor'])@np.array(source['road']);ext=d['catalog'][source['blueprint']]
        selected=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3);codes=np.floor(local*10).astype(int);ids=(codes[:,0]+120)*161*27+(codes[:,1]+80)*27+codes[:,2]-3;selected&=~((local[:,2]<3)&np.isin(ids,bg['layouts'][str(source['layout'])]['codes']));pts=local[selected];labels=raw['id'][selected];cells={}
        for i,key in enumerate(map(tuple,np.floor(pts[:,:2]/.2).astype(int))):cells.setdefault(key,[]).append(i)
        todo=set(cells);groups=[];detail=[];cc=[]
        while todo:
            seed=min(todo);todo.remove(seed);stack=[seed];indices=[]
            while stack:
                key=stack.pop();indices.extend(cells[key])
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        other=(key[0]+dx,key[1]+dy)
                        if other in todo:todo.remove(other);stack.append(other)
            indices=np.array(indices);pp=pts[indices];lo=pp.min(0);hi=pp.max(0)
            if len(pp)<3 or max(hi[:2]-lo[:2])>2*math.sqrt(sum(x*x for x in ext))+.2 or hi[2]-lo[2]>2*ext[2]+.2:continue
            cm=np.unique(np.rint(pp[:,:2]*100).astype(np.int32),axis=0);groups.append(canonical(cm));cc.append((lo[:2]+hi[:2])/2);target=labels[indices]==source['actor_id'];detail.append((len(pp),int(target.sum()),bool(target.all()),len(cm)))
        assert sorted(groups)==sorted(canonical(g) for g in saved['groups_cm'])
        assert sorted(detail)==sorted((g['points'],g['target_returns'],g['all_target'],g['quantized_points']) for g in saved['group_diagnostics'])
        np.testing.assert_allclose(sorted(map(tuple,cc)),sorted(map(tuple,np.array(front['variants'][0]['centers']).reshape(-1,2))),rtol=0,atol=1e-10)
        # Decimal exact binary inputs and independent squared-radius membership.
        with localcontext() as ctx:
            ctx.prec=80;xy=[Decimal.from_float(float(v))*1000000 for v in source['true_xy']];body_radius=math.ceil(math.sqrt(sum(x*x for x in ext))*1e6);assert body_radius==saved['body_um'] and saved['point_quantization_allowance_um']==8000;base_radius=body_radius+8000;gs=[];zero=[];fitted=[]
            for g in saved['groups_cm']:
                distances=[sum((Decimal(int(point[j])*10000)-xy[j])**2 for j in (0,1)) for point in g];score=max(0,max(int(s.sqrt().to_integral_value(rounding=ROUND_CEILING)) for s in distances)-base_radius);gs.append(score);zero.append(all(s<=base_radius*base_radius for s in distances));fit=base_radius+body['registry'][source['blueprint']]['development_slack_um'];fitted.append(all(s<=fit*fit for s in distances));point_checks+=len(distances);group_checks+=1
        assert gs==[g['support_score_um'] for g in saved['group_diagnostics']];score=min(gs) if gs else 0;assert score==saved['score_um'] and saved['available']==bool(groups)==front['variants'][0]['available'];assert saved['zero_slack_covered']==(not groups or any(zero))
        if source['split']=='test':assert saved['fitted_covered']==(not groups or any(fitted))
        assert saved['centroid_model_covered']==front['variants'][0]['covered'];ep_scores[source['episode_id']]=max(ep_scores.get(source['episode_id'],0),score);checks.append(dict(id=source['id'],blueprint=source['blueprint'],episode_id=source['episode_id'],split=source['split'],available=bool(groups),score_um=score,zero_slack_covered=not groups or any(zero),fitted_covered=not groups or any(fitted),centroid_model_covered=saved['centroid_model_covered']))
        if len(checks)%500==0:print('body audited',len(checks),flush=True)
    for bp in d['catalog']:
        scores=[ep_scores.get(e['episode']['id'],0) for e in parent['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(scores)==95 and max(scores)==body['registry'][bp]['development_slack_um']
        rr=[r for r in checks if r['blueprint']==bp and r['split']=='test'];summary=next(x for x in body['summary'] if x['blueprint']==bp);assert summary['fitted_support_excluded_episodes']==len({r['episode_id'] for r in rr if not r['fitted_covered']});assert summary['zero_slack_excluded_episodes']==len({r['episode_id'] for r in rr if not r['zero_slack_covered']})
    out=dict(frame_checks=checks,frames=len(checks),group_checks=group_checks,quantized_point_checks=point_checks,source_sha256=sha(Path(__file__)),body_source_sha256=sha(E/'body_support.py'),body_sha256=sha(a.body),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent BFS complete component/point-set reconstruction and Decimal score/coverage. Hypothesis development only; no expiry, tightness, paid utility, prospective risk or physical-world identifiability claim.')
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('complete',len(checks),flush=True)
if __name__=='__main__':main()
