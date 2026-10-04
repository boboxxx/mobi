#!/usr/bin/env python3
"""Independent rational score/set reconstruction on previously audited inputs."""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F

ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
sys.path.insert(0,str(ROOT/'experiments/prospective_hypotheses_20261004'))
spec=importlib.util.spec_from_file_location('parent_balanced_independent',ROOT/'experiments/prospective_hypotheses_20261004/audit.py')
fresh=importlib.util.module_from_spec(spec);spec.loader.exec_module(fresh)
local=fresh.local
FAMILIES=('balanced_mean','balanced_modes')
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    freeze=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in freeze[section].items():assert sha(ROOT/n)==h,n
    data=read(P/'development_sheng.json');old=read(ROOT/'results/prospective_hypotheses_20261004/qualification_sheng.json');source={r['id']:r for r in old['rows']}
    assert data['parent_sha256']==sha(ROOT/'results/prospective_hypotheses_20261004/qualification_sheng.json') and not data['fresh_qualification'] and data['freeze_sha256']==sha(E/'freeze.json')
    assert [r['id'] for r in data['rows']]==list(source)
    dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'];events=defaultdict(lambda:F(0));checks=0;over=[]
    for i,row in enumerate(data['rows']):
        r=source[row['id']];ext=old['catalog'][r['blueprint']];b=local.params(ext)[0];pred=r['prediction'];hh=r['hulls_cm'];tables=local.projected(hh,dirs)
        pose=local.pose_score(tables,dirs,ext,r['true_xy']);body=fresh.portable.body_score(r['groups_cm'],b+8000,r['true_xy']) if hh else 0
        for family in FAMILIES:
            supported=pred['status']=='supported';centers=([pred['mean_um']] if family=='balanced_mean' else pred['centers_um']) if supported else []
            scale=pred['single_scale_um' if family=='balanced_mean' else 'modes_scale_um'] if supported else max(50000,b)
            residual=min(local.err(c,r['true_xy']) for c in centers) if supported else body
            s=F(max(pose,residual),scale) if hh else F(0);assert row['scores'][family]==[s.numerator,s.denominator]
            events[r['episode_id'],family]=max(events[r['episode_id'],family],s)
            if r['split']!='test':continue
            q=F(*data['registry'][r['blueprint']][family]);radius=local.up(q*scale);v=row['methods'][family]
            if not hh:expected=dict(status='refused',lower_us=[],kind='empty_observation')
            elif not supported:
                fact=dict(r,geometries={'joint':v['joint_geometry']});g=fresh.geometry(fact,'joint',F(radius),ext,dirs)
                expected=dict(**g,kind='fallback_joint',unit_um=scale,radius_um=radius)
            else:
                rects=local.rectangle_list(tables,dirs,ext,radius);ages=[]
                if rects:
                    for query in ((-6000000,0),(6000000,0)):
                        d=max(local.floorroot(min(local.squared(rect,query,dirs) for rect in rects)),min(local.circle(c,radius,query) for c in centers));ages.append(local.age(d,b))
                expected=dict(status='bounded' if rects else 'empty',lower_us=ages,kind='supported_intersection',unit_um=scale,radius_um=radius)
                if s<=q:
                    point=[F.from_float(float(x))*1000000 for x in r['true_xy']]
                    assert any(local.squared(rect,point,dirs)==0 for rect in rects)
                    assert any(sum((c[j]-point[j])**2 for j in (0,1))<=radius**2 for c in centers)
            assert all(v[k]==value for k,value in expected.items()),(r['id'],family)
            if v['status']=='bounded':
                for j,(age,oracle) in enumerate(zip(v['lower_us'],r['oracle_us'])):
                    if age>oracle:over.append([r['id'],family,j,age,oracle])
                    if s<=q:assert age<=oracle
            checks+=1
        if (i+1)%500==0:print('independently audited',i+1,flush=True)
    for bp in old['catalog']:
        cal=[e['episode'] for e in old['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration']
        for family in FAMILIES:
            q=max(events[e['id'],family] for e in cal);assert data['registry'][bp][family]==[q.numerator,q.denominator]
    for summary in data['summary']:
        bp=summary['blueprint'];family=summary['family'];eps=[e['episode'] for e in old['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];q=F(*data['registry'][bp][family]);assert summary['excluded_episodes']==[e['id'] for e in eps if events[e['id'],family]>q]
        rows=[r for r in data['rows'] if r['blueprint']==bp and r['split']=='test'];gaps=[];overs=[];above=below=0
        for r in rows:
            ref=source[r['id']];v=r['methods'][family];ages=v['lower_us'] if v['status']=='bounded' else [0,0];old_v=ref['geometries']['local_mean' if family=='balanced_mean' else 'local_modes'];old_age=old_v['lower_us'] if old_v['status']=='bounded' else [0,0]
            for j,(a,o,vv) in enumerate(zip(ages,ref['oracle_us'],old_age)):
                gaps.append(max(0,o-a));above+=a>vv;below+=a<vv
                if a>o:overs.append([r['id'],j,a,o])
        gaps.sort();pos=F((len(gaps)-1)*95,100);j=pos.numerator//pos.denominator;p95=float(gaps[j]+(gaps[min(j+1,len(gaps)-1)]-gaps[j])*(pos-j))
        assert summary['oracle_gap_us_p95']==p95 and summary['age_overstatements']==overs and summary['above_old']==above and summary['below_old']==below and summary['source_queries']==len(gaps)
    out=dict(rows=len(data['rows']),independent_geometry_checks=checks,age_overstatements=over,development_sha256=sha(P/'development_sheng.json'),source_sha256=sha(E/'audit.py'),fresh_qualification=False,scope='Independent rational body/pose scores, scale units, supported rectangle/circle distance and containment, fallback primal/dual certificates, planned maxima and source-age outcomes. Parent raw-input audit and shared predictor replay inherited; no fresh risk or paid policy certification.')
    args.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('FINITE_BALANCED_INDEPENDENT_AUDIT_COMPLETE',flush=True)
if __name__=='__main__':main()
