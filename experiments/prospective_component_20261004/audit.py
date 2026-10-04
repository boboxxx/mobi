#!/usr/bin/env python3
"""Independent raster, rational sets, actual wires, epochs and three-FIFO audit.

The learned feature/predictor replay is explicitly shared. Geometry, scores,
label rounding, calibration and policy replay use archived independent auditors.
"""
import bootstrap
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
FAMILIES=('joint','ridge','local_mean','local_modes','supported_mean','supported_modes','fallback_um')
PRIMARY=('joint','ridge','local_mean','local_modes','component_mean','component_modes')
KINDS=('function','deadline');METHODS=tuple(f+'_'+k for f in PRIMARY for k in KINDS)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
def expand(wire):
    b=zlib.decompress(wire);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:];return json.loads(b[:-32])
def expected_state(pred,center,family):
    family=family.replace('component_','local_')
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
    out.update(supported_mean=out['local_mean'] if pred['status']=='supported' else F(0),supported_modes=out['local_modes'] if pred['status']=='supported' else F(0),fallback_um=out['joint'] if pred['status']!='supported' else F(0))
    return out
def geometry(r,family,q,extent,dirs):
    if family.startswith('component_'):
        actual=r['geometries'][family]
        if not r['hulls_cm']:return dict(status='refused',lower_us=[])
        if r['prediction']['status']!='supported':return geometry(dict(r,geometries={'joint':actual['joint_geometry']}),'joint',F(q['fallback_um']),extent,dirs)
        g=local.independent_infer(r['hulls_cm'],extent,r['prediction'],q['supported'],family.replace('component_','local_'),'max',dirs)
        assert all(actual['geometry'][k]==v for k,v in g.items())
        return dict(status=g['status'],lower_us=g['lower_us'])
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

def threshold(registry,bp,family):
    if family.startswith('component_'):return dict(supported=F(*registry[bp]['supported_'+family[len('component_'):]]),fallback_um=int(F(*registry[bp]['fallback_um'])))
    return F(*registry[bp][family])
def failed(ss,family,registry):
    if family.startswith('component_'):return ss['supported_'+family[len('component_'):]]>F(*registry['supported_'+family[len('component_'):]]) or ss['fallback_um']>F(*registry['fallback_um'])
    return ss[family]>F(*registry[family])
def audit_policy(d):
    from scipy.stats import beta
    policy=read(P/'policy_frozen.json');paid=read(P/'paid_certification_sheng.json');plan=read(E/'plan.json');episodes=[e for e in plan if e['split']=='certification'];rows={r['id']:r for r in d['rows']};traces={(t['episode_id'],t['method'],t['rate'],t['startup']):t for t in paid['traces']};delta=F(1,3840);accepted=0;seen=set()
    assert policy['policies']==48 and policy['binary_tests']==96 and policy['risk_target']==[1,20] and policy['confidence_error_budget']==[1,40] and policy['certification_complete'] and policy['test_clouds_processed_before_certificate']==0
    assert policy['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and policy['qualification_sha256']==sha(P/'qualification_certification_sheng.json') and policy['paid_sha256']==sha(P/'paid_certification_sheng.json') and policy['model_freeze_sha256']==sha(E/'freeze.json')
    for cell in policy['cells']:
        key=(cell['family'],cell['kind'],cell['rate'],cell['startup']);assert key not in seen;seen.add(key);assert cell['family'] in PRIMARY and cell['kind'] in KINDS and cell['rate'] in (20000000,2000000) and cell['startup'] in ('warm','cold');evidence=[]
        for ep in episodes:
            tr=traces[ep['id'],cell['family']+'_'+cell['kind'],cell['rate'],cell['startup']];dec=tr['decisions'][ep['selected_query_index']];assert dec['step']*2+dec['query']==ep['selected_query_index'];g=bool(dec['grant']);f=a=False
            if g:
                fact=rows[dec['fact_id']];ss={m:F(*q) for m,q in fact['scores'].items()};f=failed(ss,cell['family'],d['registry'][fact['blueprint']]);a=dec['now_us']+220000-fact['source_us']>fact['oracle_us'][dec['query']]
            evidence.append(dict(episode_id=ep['id'],query_index=ep['selected_query_index'],grant=g,excluded=f,action_failed=a,fact_id=dec['fact_id']))
        assert cell['evidence']==evidence;both=True
        for name,field in [('center_score','excluded'),('source_action','action_failed')]:
            n=sum(e['grant'] for e in evidence);k=sum(e[field] for e in evidence);c=cell['certificates'][name];p=sum(F(math.comb(n,j))*F(1,20)**j*F(19,20)**(n-j) for j in range(k+1)) if n else F(1);ok=bool(n and p<=delta);upper=F(*c['conditional_upper']);reference=1.0 if not n or n==k else float(beta.isf(float(delta),k+1,n-k))
            assert c['authorized_episodes']==n and c['failed_authorized_episodes']==k and c['planned_episodes']==600 and c['p_value']==[p.numerator,p.denominator] and c['accepted']==ok and c['family_count']==96 and c['risk_target']==[1,20] and abs(float(upper)-reference)<=1e-12;both=both and ok
        assert cell['accepted']==both;accepted+=both
    assert len(seen)==48 and policy['accepted_policies']==accepted and policy['zero_failure_selected_queries_required']==161
    return dict(policies=48,binary_tests=96,accepted=accepted,certificate_sha256=sha(P/'policy_frozen.json'),independent_selected_query_and_exact_p_value_checks=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--qualification-only',action='store_true');a=ap.parse_args();receipt=read(P/'calibration_frozen.json');cert=read(P/'qualification_certification_sheng.json');test=read(P/'qualification_test_sheng.json');plan=read(E/'plan.json');records=read(P/'capture/record.json');eps=read(P/'capture/episodes.json');d=dict(test,rows=receipt['rows']+cert['rows']+test['rows'],episodes=eps,episode_scores=dict(receipt['calibration_episode_scores'],**cert['episode_scores'],**test['episode_scores']));manifest=read(P/'capture/manifest.json');bg=read(ROOT/'results/background_frontend_20261004/background.json');dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'];pose.verify_grid(dirs);models=load_models()
    for file in ('freeze.json',):
        f=read(E/file)
        for section in ('sources','inputs'):
            for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert d['catalog']==read(E/'catalog.json') and d['basis']==bg['basis'] and len(plan)==2520 and [e['episode'] for e in eps]==plan and eps==d['episodes'];assert [r['id'] for r in records]==[r['id'] for r in d['rows']] and len(set(r['id'] for r in records))==len(records)
    for file,key in (('capture.py','source_sha256'),('plan.json','plan_sha256'),('PROTOCOL.md','protocol_sha256')):assert manifest[key]==sha(E/file)
    assert d['capture_manifest_sha256']==sha(P/'capture/manifest.json') and d['model_freeze_sha256']==receipt['model_freeze_sha256']==sha(E/'freeze.json') and d['measurement_freeze_sha256']==receipt['measurement_freeze_sha256']==sha(E/'freeze.json')
    assert d['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and receipt['registry']==d['registry'] and receipt['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest();assert receipt['calibration_n_per_class']==260 and receipt['component_exclusion_target']==[1,40] and receipt['baseline_exclusion_target']==[1,20]
    confidence=18*F(39,40)**260+24*F(19,20)**260;assert receipt['confidence_error_bound']==[confidence.numerator,confidence.denominator] and confidence<=F(1,40)
    for split,stage in [('certification',cert),('test',test)]:
        assert stage['registry']==receipt['registry'] and stage['calibration_receipt_sha256']==sha(P/'calibration_frozen.json')
        order=read(P/('order_'+split+'.json'));assert order==dict(split=split,calibration_receipt_sha256=sha(P/'calibration_frozen.json'),policy_receipt_sha256=sha(P/'policy_frozen.json') if split=='test' else None,stage_clouds_read=0,receipt_written_before_stage_processing=True)
    # Independent integer RNG/metadata reconstruction (not calling make_plan).
    def validate_scene(e,rng,bp,split,index,seed):
        vals=[int(rng.randint(-8000000,8000001)),int(rng.randint(-4000000,4000001)),int(rng.randint(0,360000)),int(rng.randint(500000,1800001) if bp.startswith('walker.') else rng.randint(1000000,3000001))]
        assert e['integer_scene']==vals and [e[k] for k in ('longitudinal_m','lateral_m','yaw_deg','target_speed_mps')]==[vals[0]/1000000,vals[1]/1000000,vals[2]/1000,vals[3]/1000000]
        assert e['blueprint']==bp and e['split']==split and e['index']==index and e['seed']==seed and e['id']=='freshcomponent_'+bp.replace('.','_')+'_'+split+'_%04d'%index
    for ci,bp in enumerate(d['catalog']):
        for split,n,seed in [('calibration',260,2026104700+ci),('test',60,2026104900+ci)]:
            rng=np.random.RandomState(seed);items=[e for e in plan if e['blueprint']==bp and e['split']==split];assert len(items)==n
            for i,e in enumerate(items):validate_scene(e,rng,bp,split,i,seed)
    rng=np.random.RandomState(2026104800);selector=np.random.RandomState(2026104801);items=[e for e in plan if e['split']=='certification'];assert len(items)==600
    for i,e in enumerate(items):
        bp=list(d['catalog'])[int(rng.randint(0,6))];validate_scene(e,rng,bp,'certification',i,2026104800);assert e['selected_query_index']==int(selector.randint(0,32))
    source={r['id']:r for r in records};epmap={e['episode']['id']:e for e in eps};byep=defaultdict(list);ep_scores=defaultdict(lambda:F(0));points=geometry_checks=0;max_affine=F(0);excluded=[];over=[]
    for i,r in enumerate(d['rows']):
        ep=epmap[r['episode_id']];snap=ep['trajectory'][r['step']];assert snap['frame']==r['frame'] and snap['timestamp']==r['timestamp'] and snap['center']==r['center']
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
                m=key;q=threshold(d['registry'],r['blueprint'],m);out=geometry(r,key,q,extent,dirs);assert all(actual[k]==v for k,v in out.items()),(r['id'],key)
                if pred['status']=='supported' and key in ('local_mean','local_modes','component_mean','component_modes'):
                    mode=key.rsplit('_',1)[1];sq=q['supported'] if isinstance(q,dict) else q;active_score=ss['supported_'+mode] if key.startswith('component_') else ss[key]
                    if active_score<=sq:
                        point=[F.from_float(float(x))*1000000 for x in r['true_xy']];rects=local.rectangle_list(local.projected(r['hulls_cm'],dirs),dirs,extent,local.up(sq*10000));centers=[pred['mean_um']] if mode=='mean' else pred['centers_um'];radius=local.up(sq*pred['single_scale_um' if mode=='mean' else 'modes_scale_um'])
                        assert any(local.squared(rect,point,dirs)==0 for rect in rects) and any(sum((c[j]-point[j])**2 for j in (0,1))<=radius**2 for c in centers)
                if failed(ss,m,d['registry'][r['blueprint']]):excluded.append([r['id'],key])
                if actual['status']=='bounded':
                    for j,(t,o) in enumerate(zip(actual['lower_us'],oracle)):
                        if t>o:over.append([r['id'],key,j,t,o])
                        if not failed(ss,m,d['registry'][r['blueprint']]):assert t<=o,(r['id'],key,j,t,o)
                geometry_checks+=1
        byep[r['episode_id']].append(r)
        if (i+1)%500==0:print('audited geometry',i+1,flush=True)
    all_scores={e['id']:{m:[ep_scores[(e['id'],m)].numerator,ep_scores[(e['id'],m)].denominator] for m in FAMILIES} for e in plan};assert d['episode_scores']==all_scores and receipt['calibration_episode_scores']=={e['id']:all_scores[e['id']] for e in plan if e['split']=='calibration'}
    cal_ids={str((P/'capture'/r['cloud_file']).relative_to(ROOT)) for r in records if r['split']=='calibration'};assert set(receipt['input_hashes'])==cal_ids
    for bp in d['catalog']:
        cal=[e for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(cal)==260
        for m in FAMILIES:
            q=max(ep_scores[(e['id'],m)] for e in cal);assert d['registry'][bp][m]==[q.numerator,q.denominator]
    cleanup=read(P/'capture/cleanup.json');assert cleanup['vehicles']==cleanup['walkers']==cleanup['sensors']==0 and not cleanup['synchronous'] and read(P/'server_stopped.json')['stopped']
    out=dict(frames=len(d['rows']),quantized_point_checks=points,independent_geometry_checks=geometry_checks,shared_prediction_replays=len(d['rows']),excluded_noncal_frame_methods=excluded,age_overstatements=over,maximum_affine_error_um=[(max_affine*1000000).numerator,(max_affine*1000000).denominator],certification_qualification_sha256=sha(P/'qualification_certification_sheng.json'),test_qualification_sha256=sha(P/'qualification_test_sheng.json'),calibration_receipt_sha256=sha(P/'calibration_frozen.json'),source_sha256=sha(Path(__file__)),qualification_only=a.qualification_only)
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
    if not a.qualification_only:
        out['paid_audits']={}
        for split in ('certification','test'):
            detail={};audit_paid(d,epmap,byep,detail,split);out['paid_audits'][split]=detail
        out['policy_audit']=audit_policy(cert)
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('FINITE_INDEPENDENT_COMPONENT_AUDIT_COMPLETE',len(d['rows']),flush=True)
def audit_paid(d,epmap,qualified_byep,out,split):
    paid=read(P/('paid_'+split+'_sheng.json'));ctx=paid['registration'];assert paid['qualification_sha256']==sha(P/('qualification_'+split+'_sheng.json')) and paid['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and paid['measurement_freeze_sha256']==sha(E/'freeze.json')
    assert ctx['catalog']==d['catalog'] and ctx['registry']==d['registry'] and ctx['calibration_receipt_sha256']==sha(P/'calibration_frozen.json') and ctx['calibration_sha256']==hashlib.sha256(canon(d['registry'])).hexdigest() and paid['contract_sha256']==hashlib.sha256(canon(ctx)).hexdigest()
    runtime_names=('experiments/prospective_component_20261004/bootstrap.py', 'experiments/prospective_component_20261004/fresh_transport.py', 'experiments/prospective_component_20261004/fresh_inference.py', 'experiments/prospective_component_20261004/fresh_io.py', 'experiments/component_expiry_20261004/method.py', 'experiments/prospective_hypotheses_20261004/transport.py', 'experiments/prospective_hypotheses_20261004/inference.py', 'experiments/prospective_hypotheses_20261004/io_common.py', 'experiments/prospective_hypotheses_20261004/scores.py', 'experiments/calibrated_hypotheses_20261004/model.py', 'experiments/calibrated_hypotheses_20261004/geometry.py', 'experiments/state_predictor_20261004/predictor.py', 'experiments/state_predictor_20261004/integer_state.py', 'experiments/pose_support_20261004/observer.py', 'experiments/pose_support_20261004/directions.json', 'experiments/body_expiry_20261004/frontend.py', 'experiments/body_expiry_20261004/kernel.py', 'experiments/body_expiry_20261004/proposer.cpp')
    f=read(E/'freeze.json');assert ctx['installed_sources']=={n:f['sources'][n] for n in runtime_names} and ctx['source_model_hashes']=={n:h for n,h in f['inputs'].items() if n.endswith('models_sheng.json')};assert ctx['version']==1 and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['query_radius_um']==750000 and ctx['cap_us']==500000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000)
    s=paid['setup'];wire=(P/('setup_'+split+'.bin')).read_bytes();assert len(wire)==s['wire_bytes'] and sha(P/('setup_'+split+'.bin'))==s['wire_sha256'] and expand(wire)==ctx and len(s['samples'])==3
    for dest,key in (('source_us','source_s'),('receiver_us','receiver_s')):assert s[dest]==math.ceil(max(v[key] for v in s['samples'])*1e6)
    qq={r['id']:r for r in d['rows'] if r['split']==split};assert [r['id'] for r in paid['rows']]==list(qq);byep=defaultdict(list);packet_checks=0
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
    traces=paid['traces'];assert len(traces)==(600 if split=='certification' else 360)*len(METHODS)*4;seen=set();grants=grid=conflicts=0
    for tr in traces:
        key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);assert tr['method'] in METHODS and tr['rate'] in (20000000,2000000) and tr['startup'] in ('warm','cold');ep=epmap[tr['episode_id']];assert ep['episode']['split']==split and tr['blueprint']==ep['episode']['blueprint'] and tr['capture_status']==ep['status'];rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['t0']==t0
        expected=body.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==v for k,v in expected.items())
        for dec in tr['decisions']:
            if not dec['grant']:continue
            grants+=1;fact=qq[dec['fact_id']];body_um=local.params(d['catalog'][fact['blueprint']])[0];qx=(-6000000,6000000)[dec['query']]
            for snap in ep['trajectory']:
                stamp=math.floor(snap['timestamp']*1e6)
                if dec['now_us']<=stamp<=dec['now_us']+220000:
                    xy=(np.asarray(snap['center'])-d['basis']['anchor'])@np.asarray(d['basis']['road']);grid+=1;conflicts+=math.hypot(xy[0]*1e6-qx,xy[1]*1e6)<=body_um+750000
    out.update(actual_packet_checks=packet_checks,trace_checks=len(traces),decision_checks=len(traces)*32,grants=grants,observed_future_grid_checks=grid,observed_future_grid_violations=conflicts,paid_sha256=sha(P/('paid_'+split+'_sheng.json')),scope='Shared learned prediction replay; independent full-XYZ raster, exact hull inclusion, rational scores/sets/age, all planned max260 registries, actual wires/fees/source epochs and three FIFO replay. Future grid is diagnostic, not continuous safety or live radio/ego. Conditional-grant certificate is separately audited.')
if __name__=='__main__':main()
