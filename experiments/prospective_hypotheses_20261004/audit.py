#!/usr/bin/env python3
"""Independent raster, rational sets, actual wires, epochs and three-FIFO audit.

The learned feature/predictor replay is explicitly shared. Geometry, scores,
label rounding, calibration and policy replay use archived independent auditors.
"""
import argparse,hashlib,importlib.util,json,math,zlib
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from scores import load_models,predictions
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
local=module('fresh_independent_local','experiments/calibrated_hypotheses_20261004/audit_development.py')
portable=module('fresh_independent_affine','experiments/prospective_shape_20261004/audit_portable_v2.py')
pose=portable.ind;body=pose.old_audit
FAMILIES=('joint','ridge','local_mean','local_modes')
KINDS=('function','deadline');METHODS=tuple(f+'_'+k for f in FAMILIES for k in KINDS)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
def expand(wire):
    b=zlib.decompress(wire);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:];return json.loads(b[:-32])
def expected_state(pred,center,family):
    if family=='joint':return {}
    if family=='ridge':return dict(center_um=center)
    out=dict(status=pred['status'])
    if pred['status']=='supported':
        if family=='local_mean':out.update(mean_um=pred['mean_um'],single_scale_um=pred['single_scale_um'])
        else:out.update(centers_um=pred['centers_um'],modes_scale_um=pred['modes_scale_um'])
    return out
def scores(gg,hh,extent,pred,center,xy,dirs):
    if not gg:return {m:F(0) for m in FAMILIES}
    ps=local.pose_score(local.projected(hh,dirs),dirs,extent,xy);joint=max(ps,portable.body_score(gg,local.params(extent)[0]+8000,xy));out=dict(joint=F(joint),ridge=F(local.err(center,xy)))
    for m in ('local_mean','local_modes'):
        s=F(ps,10000)
        if pred['status']=='supported':
            centers=[pred['mean_um']] if m=='local_mean' else pred['centers_um'];scale=pred['single_scale_um'] if m=='local_mean' else pred['modes_scale_um'];s=max(s,F(min(local.err(c,xy) for c in centers),scale))
        out[m]=s
    return out
def geometry(r,family,q,extent,dirs):
    gg=r['groups_cm'];hh=r['hulls_cm'];pred=r['prediction'];b=local.params(extent)[0]
    if family=='ridge':
        if not gg:return dict(status='refused',lower_us=[])
        return dict(status='bounded',lower_us=[local.age(max(0,local.floorroot(sum(F(v-w)**2 for v,w in zip(r['ridge_center_um'],query)))-int(q)),b) for query in ((-6000000,0),(6000000,0))])
    if family!='joint':
        m,variant=(family,'max') if family in ('local_mean','local_modes') else family.rsplit('_',1)
        return local.independent_infer(hh,extent,pred,q,m,variant,dirs)
    actual=r['geometries']['joint'];param=pose.constants(extent,int(q));ranges=pose.all_point_ranges(gg,dirs);rects=pose.rectangles(ranges,dirs,param);qq=pose.exact_pose_geometry(rects,dirs,b);status='refused' if not gg else 'empty' if not rects else 'bounded';pg=dict(status=status,queries=qq or [],feasible_cells=len(rects));assert actual['pose']==pg
    ss=pose.check_sphere(actual['sphere'],gg,hh,b+8000+int(q),b);pp=[v['lower_us'] for v in qq] if qq else [];ss_status=actual['sphere']['status'];js='empty' if 'empty' in (status,ss_status) else 'bounded' if pp or ss else 'refused';aa=[max(v) for v in zip(*[v for v in (pp,ss) if v])] if js=='bounded' else []
    return dict(status=js,lower_us=aa)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--qualification-only',action='store_true');a=ap.parse_args();d=read(P/'qualification_sheng.json');receipt=read(P/'calibration_frozen.json');plan=read(E/'plan.json');records=read(P/'capture/record.json');eps=read(P/'capture/episodes.json');manifest=read(P/'capture/manifest.json');bg=read(ROOT/'results/background_frontend_20261004/background.json');dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'];pose.verify_grid(dirs);models=load_models()
    for file in ('freeze.json','measurement_freeze.json'):
        f=read(E/file)
        for section in ('sources','inputs'):
            for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert d['catalog']==read(E/'catalog.json') and d['basis']==bg['basis'] and len(plan)==1110 and [e['episode'] for e in eps]==plan and eps==d['episodes'];assert [r['id'] for r in records]==[r['id'] for r in d['rows']] and len(set(r['id'] for r in records))==len(records)
    for file,key in (('capture.py','source_sha256'),('plan.json','plan_sha256'),('PROTOCOL.md','protocol_sha256')):assert manifest[key]==sha(E/file)
    assert d['capture_manifest_sha256']==sha(P/'capture/manifest.json') and d['model_freeze_sha256']==receipt['model_freeze_sha256']==sha(E/'freeze.json') and d['measurement_freeze_sha256']==receipt['measurement_freeze_sha256']==sha(E/'measurement_freeze.json')
    assert d['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and receipt['registry']==d['registry'] and receipt['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest();assert receipt['calibration_n_per_class']==125 and receipt['simultaneous_family_class_count']==24 and receipt['calibration_confidence_lower']==1-24*.95**125
    assert read(P/'qualification_order.json')==dict(calibration_receipt_sha256=sha(P/'calibration_frozen.json'),test_clouds_read=0,receipt_written_before_test_processing=True)
    # Verify law without requiring NumPy1/2's walker affine rounding to coincide.
    for ci,bp in enumerate(d['catalog']):
        for split,n,seed in (('calibration',125,2026104100+ci),('test',60,2026104200+ci)):
            rng=np.random.RandomState(seed);items=[e for e in plan if e['blueprint']==bp and e['split']==split];assert len(items)==n
            for i,e in enumerate(items):
                vals=[float(rng.uniform(-8,8)),float(rng.uniform(-4,4)),float(rng.uniform(0,360)),float(rng.uniform(.5,1.8) if bp.startswith('walker.') else rng.uniform(1,3))];vv=[e[k] for k in ('longitudinal_m','lateral_m','yaw_deg','target_speed_mps')];assert vv[:3]==vals[:3] and e['index']==i and e['seed']==seed
                assert vv[3]==vals[3] or (bp.startswith('walker.') and abs(F.from_float(vv[3])-F.from_float(vals[3]))<=F.from_float(float(np.spacing(max(abs(vv[3]),abs(vals[3]))))))
    source={r['id']:r for r in records};epmap={e['episode']['id']:e for e in eps};byep=defaultdict(list);ep_scores=defaultdict(lambda:F(0));points=geometry_checks=0;max_affine=F(0);excluded=[];over=[]
    for i,r in enumerate(d['rows']):
        old=source[r['id']];assert all(r[k]==v for k,v in old.items());p=P/'capture'/old['cloud_file'];assert sha(p)==old['cloud_sha256'];assert old['points']==math.ceil(old['original_points']/4) and old['selection_s']>0 and old['sensor_frame']==old['frame']
        with np.load(p) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform'];assert float(z['timestamp'])==old['timestamp']
        extent=d['catalog'][r['blueprint']];assert T.tolist()==old['sensor_transform']['matrix'] and old['bounding_box']['extent']==extent and old['bounding_box']['rotation']==[0.,0.,0.];max_affine=max(max_affine,portable.affine_error(old['center'],d['basis'],r['true_xy']));assert r['source_us']==math.floor(old['timestamp']*1e6) and r['acquisition_us']==math.ceil(old['acquisition_s']*1e6)
        gg=body.raster(xyz,T,d['basis'],extent,bg['layouts'][str(r['layout'])]['codes']);assert sorted(map(body.canonical,gg))==sorted(map(body.canonical,r['groups_cm'])) and len(r['groups_cm'])==len(r['hulls_cm'])
        for g,h in zip(r['groups_cm'],r['hulls_cm']):body.check_hull(g,h);points+=len(g)
        pred,center=predictions(r['hulls_cm'],r['layout'],r['blueprint'],models);assert pred==r['prediction'] and center==r['ridge_center_um'];ss=scores(r['groups_cm'],r['hulls_cm'],extent,pred,center,r['true_xy'],dirs);assert r['scores']=={m:[s.numerator,s.denominator] for m,s in ss.items()}
        for m,s in ss.items():ep_scores[(r['episode_id'],m)]=max(ep_scores[(r['episode_id'],m)],s)
        if r['split']=='calibration':assert receipt['input_hashes'][str(p.relative_to(ROOT))]==old['cloud_sha256']
        else:
            b=local.params(extent)[0];xy=[F.from_float(float(v))*1000000 for v in r['true_xy']];oracle=[local.age(local.floorroot(sum((v-w)**2 for v,w in zip(xy,query))),b) for query in ((-6000000,0),(6000000,0))];assert oracle==r['oracle_us']
            for key,actual in r['geometries'].items():
                m=key if key in FAMILIES else key.rsplit('_',1)[0];q=F(*d['registry'][r['blueprint']][m]);out=geometry(r,key,q,extent,dirs);assert all(actual[k]==v for k,v in out.items()),(r['id'],key)
                if ss[m]>q:excluded.append([r['id'],key])
                if actual['status']=='bounded':
                    for j,(t,o) in enumerate(zip(actual['lower_us'],oracle)):
                        if t>o:over.append([r['id'],key,j,t,o])
                        if ss[m]<=q:assert t<=o,(r['id'],key,j,t,o)
                geometry_checks+=1
        byep[r['episode_id']].append(r)
        if (i+1)%500==0:print('audited geometry',i+1,flush=True)
    all_scores={e['id']:{m:[ep_scores[(e['id'],m)].numerator,ep_scores[(e['id'],m)].denominator] for m in FAMILIES} for e in plan};assert d['episode_scores']==all_scores and receipt['calibration_episode_scores']=={e['id']:all_scores[e['id']] for e in plan if e['split']=='calibration'}
    cal_ids={str((P/'capture'/r['cloud_file']).relative_to(ROOT)) for r in records if r['split']=='calibration'};assert set(receipt['input_hashes'])==cal_ids
    for bp in d['catalog']:
        cal=[e for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(cal)==125
        for m in FAMILIES:
            q=max(ep_scores[(e['id'],m)] for e in cal);assert d['registry'][bp][m]==[q.numerator,q.denominator]
    cleanup=read(P/'capture/cleanup.json');assert cleanup['vehicles']==cleanup['walkers']==cleanup['sensors']==0 and not cleanup['synchronous'] and read(P/'server_stopped.json')['stopped']
    out=dict(frames=len(d['rows']),quantized_point_checks=points,independent_geometry_checks=geometry_checks,shared_prediction_replays=len(d['rows']),excluded_test_frame_methods=excluded,age_overstatements=over,maximum_affine_error_um=[(max_affine*1000000).numerator,(max_affine*1000000).denominator],qualification_sha256=sha(P/'qualification_sheng.json'),calibration_receipt_sha256=sha(P/'calibration_frozen.json'),source_sha256=sha(Path(__file__)),qualification_only=a.qualification_only)
    physical=[]
    for bp,ext in d['catalog'].items():
        corners=outside=motion=bad=0;maximum=0.;R=local.params(ext)[0]/1000000
        for ep in eps:
            if ep['status']!='captured' or ep['episode']['blueprint']!=bp:continue
            assert ep['bounding_box']['extent']==ext and len(ep['trajectory'])==21
            for snap in ep['trajectory']:
                for point in snap['world_vertices']:corners+=1;outside+=math.hypot(point[0]-snap['center'][0],point[1]-snap['center'][1])>R
            for row in byep[ep['episode']['id']]:
                for snap in ep['trajectory']:
                    dt=snap['timestamp']-row['timestamp']
                    if not 0<=dt<=.500001:continue
                    disp=math.hypot(snap['center'][0]-row['center'][0],snap['center'][1]-row['center'][1]);limit=5*dt+1.5*dt*dt;motion+=1;bad+=disp>limit+.000008;maximum=max(maximum,disp-limit)
        physical.append(dict(blueprint=bp,xy_corner_checks=corners,xy_outside_corners=outside,source_future_displacement_checks=motion,source_future_displacement_violations=bad,max_positive_displacement_excess_um_ceil=math.ceil(max(0,maximum)*1000000),diagnostic_precision_allowance_um=8))
    out['physical_snapshot_checks']=physical
    if not a.qualification_only:audit_paid(d,epmap,byep,out)
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('FINITE_INDEPENDENT_HYPOTHESES_AUDIT_COMPLETE',len(d['rows']),flush=True)
def audit_paid(d,epmap,qualified_byep,out):
    paid=read(P/'paid_sheng.json');ctx=paid['registration'];assert paid['qualification_sha256']==sha(P/'qualification_sheng.json') and paid['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and paid['measurement_freeze_sha256']==sha(E/'measurement_freeze.json')
    assert ctx['catalog']==d['catalog'] and ctx['registry']==d['registry'] and ctx['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and ctx['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest() and paid['contract_sha256']==hashlib.sha256(canon(ctx)).hexdigest()
    runtime_names=('experiments/prospective_hypotheses_20261004/transport.py','experiments/prospective_hypotheses_20261004/inference.py','experiments/prospective_hypotheses_20261004/io_common.py','experiments/prospective_hypotheses_20261004/scores.py','experiments/calibrated_hypotheses_20261004/model.py','experiments/calibrated_hypotheses_20261004/geometry.py','experiments/state_predictor_20261004/predictor.py','experiments/state_predictor_20261004/integer_state.py','experiments/pose_support_20261004/observer.py','experiments/pose_support_20261004/directions.json','experiments/body_expiry_20261004/frontend.py','experiments/body_expiry_20261004/kernel.py','experiments/body_expiry_20261004/proposer.cpp')
    f=read(E/'measurement_freeze.json');assert ctx['installed_sources']=={n:f['sources'][n] for n in runtime_names} and ctx['source_model_hashes']=={n:h for n,h in f['inputs'].items() if n.endswith('models_sheng.json')};assert ctx['version']==1 and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['query_radius_um']==750000 and ctx['cap_us']==500000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000)
    s=paid['setup'];wire=(P/'setup.bin').read_bytes();assert len(wire)==s['wire_bytes'] and sha(P/'setup.bin')==s['wire_sha256'] and expand(wire)==ctx and len(s['samples'])==3
    for dest,key in (('source_us','source_s'),('receiver_us','receiver_s')):assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
    qq={r['id']:r for r in d['rows'] if r['split']=='test'};assert [r['id'] for r in paid['rows']]==list(qq);byep=defaultdict(list);packet_checks=0
    for r in paid['rows']:
        ref=qq[r['id']]
        for k in ('id','episode_id','blueprint','cloud_file','cloud_sha256','layout','frame','source_us','acquisition_us','selection_s'):assert r[k]==ref[k]
        assert set(r['methods'])==set(METHODS) and len(r['measurement_order'])==3
        for i,seq in enumerate(r['measurement_order']):assert seq==sorted(METHODS,key=lambda m:hashlib.sha256((r['id']+'|'+str(i)+'|'+m).encode()).digest())
        for method,m in r['methods'].items():
            family,kind=method.rsplit('_',1);path=ROOT/m['packet'];wire=path.read_bytes();assert len(wire)==m['wire_bytes'] and sha(path)==m['wire_sha256'];obj=expand(wire);expected=dict(version=1,kind=kind,family=family,blueprint=r['blueprint'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],contract=paid['contract_sha256'],calibration=ctx['calibration_sha256']);g=ref['geometries'][family];assert m['status']==g['status'] and m['lower_us']==g['lower_us']
            if kind=='function':expected.update(hulls_cm=ref['hulls_cm'],hypothesis=expected_state(ref['prediction'],ref['ridge_center_um'],family))
            else:expected.update(status=g['status'],lower_us=g['lower_us'])
            assert obj==expected and len(m['samples'])==3 and all(v['selection_s']==r['selection_s'] and v['source_s']>=0 and v['receiver_s']>=0 for v in m['samples']);assert m['source_us']==math.ceil((max(v['source_s'] for v in m['samples'])+r['selection_s'])*1e6) and m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);packet_checks+=1
        byep[r['episode_id']].append(r)
    traces=paid['traces'];assert len(traces)==360*len(METHODS)*4;seen=set();grants=grid=conflicts=0
    for tr in traces:
        key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);assert tr['method'] in METHODS and tr['rate'] in (20000000,2000000) and tr['startup'] in ('warm','cold');ep=epmap[tr['episode_id']];assert ep['episode']['split']=='test' and tr['blueprint']==ep['episode']['blueprint'] and tr['capture_status']==ep['status'];rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['t0']==t0
        expected=body.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==v for k,v in expected.items())
        for dec in tr['decisions']:
            if not dec['grant']:continue
            grants+=1;fact=qq[dec['fact_id']];body_um=local.params(d['catalog'][fact['blueprint']])[0];qx=(-6000000,6000000)[dec['query']]
            for snap in ep['trajectory']:
                stamp=math.floor(snap['timestamp']*1e6)
                if dec['now_us']<=stamp<=dec['now_us']+220000:
                    xy=(np.asarray(snap['center'])-d['basis']['anchor'])@np.asarray(d['basis']['road']);grid+=1;conflicts+=math.hypot(xy[0]*1e6-qx,xy[1]*1e6)<=body_um+750000
    out.update(actual_packet_checks=packet_checks,trace_checks=len(traces),decision_checks=len(traces)*32,grants=grants,observed_future_grid_checks=grid,observed_future_grid_violations=conflicts,paid_sha256=sha(P/'paid_sheng.json'),scope='Shared learned prediction replay; independent full-XYZ raster, exact hull inclusion, rational scores/sets/age, all planned max125 registry, actual wires/fees/source epochs and three FIFO replay. Future grid is diagnostic, not continuous safety or live radio/ego. No conditional-grant guarantee.')
if __name__=='__main__':main()
