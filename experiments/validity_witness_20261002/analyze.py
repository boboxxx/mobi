#!/usr/bin/env python3
"""Independent full-segment witness audit. No search/native/observer import."""
import argparse,gzip,hashlib,importlib.util,json,math,sys
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('prefix_reference',ROOT/'experiments/continuity_recovery_20261002/analyze.py')
prefix=importlib.util.module_from_spec(spec);spec.loader.exec_module(prefix);body=prefix.body
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def independent_back(times,ref):
    # Exact rational integration, chronological loop, not reverse vector cumsum.
    traveled=[Fraction(0)]
    for t0,t1 in zip(times,times[1:]):
        dt=Fraction(int(t1)-int(t0),1000000);traveled.append(traveled[-1]+5*dt+Fraction(3,4)*dt*dt)
    age=Fraction(ref-int(times[-1]),1000000);end=5*age+Fraction(3,2)*age*age
    return np.asarray([float(traveled[-1]-d+end) for d in traveled])

def distances(centers,segments):
    # Unit-direction and physical along-segment distance, rather than t*delta.
    delta=segments[:,3:6]-segments[:,:3];length=np.linalg.norm(delta,axis=1)
    unit=np.divide(delta,length[:,None],out=np.zeros_like(delta),where=length[:,None]>0)
    relative=centers-segments[:,:3];along=np.clip(np.sum(relative*unit,axis=1),0,length)
    return np.linalg.norm(relative-along[:,None]*unit,axis=1)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    s=json.loads((a.results/'study/analysis.json').read_bytes());assert len(s['rows'])==36
    for field in ['source_sha256','input_sha256']:
        for f,h in s[field].items():assert sha(ROOT/f)==h,f
    oldpath=ROOT/'results/recursive_validity_20261002/study/analysis.json';old=json.loads(oldpath.read_bytes())
    for f,h in old['source_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['library_sha256']==json.loads((a.results/'build.json').read_bytes())['binary_sha256']
    assert json.loads((a.results/'build.json').read_bytes())['source_sha256']==sha(Path(__file__).with_name('segments.cpp'))
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    prefix_count=source_count=ray_checks=0;verified={};summaries=[];cached_arrays={}
    for ctx in old['contexts']:
        name=ctx['run'];capture=ROOT/'results/online_evidence_20261002/live'/name;record=json.loads(gzip.decompress((capture/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']};regions={}
        for identity in ctx['prefix_ids']:
            path=capture/'packets'/(identity+'.json');b=json.loads(path.read_bytes());d=decisions[identity]
            assert d['receiver_accepted'];scope=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            p,o,r=prefix.full_check(b['raw'],profiles,contract,scope,motion,prior=regions[b['prior']] if b['prior'] else None)
            key=sha(path);lo,hi,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(lo),tuple(hi),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name)
            assert p['reference_us']==math.ceil(d['stamp']*1e6) and p['sequence']==d['sequence']
            with np.load(capture/'clouds'/(identity+'.npz')) as cloud:original=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'])
            assert prefix.ray_keys(o,r)<=prefix.ray_keys(*original[:2]);verified[str(path.relative_to(ROOT))]=(p,o,r);prefix_count+=1
        assert key==ctx['anchor']['identity']
        for index in range(20,40):
            path=ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_drive_%03d.json'%index);raw=json.loads(path.read_bytes());scope=body.Scope(**ctx['anchor']['scope']);p,o,r=body.decode(body.canonical(raw),profiles,scope,contract);identity='drive_%03d'%index;d=decisions[identity]
            with np.load(capture/'clouds'/(identity+'.npz')) as cloud:original=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'])
            assert prefix.ray_keys(o,r)<=prefix.ray_keys(*original[:2]);assert int(r[:,4].max())==int(original[1][:,4].max());assert p['reference_us']==math.ceil(d['stamp']*1e6) and p['sequence']==d['sequence']
            verified[str(path.relative_to(ROOT))]=(p,o,r);source_count+=1
        print(json.dumps(dict(run=name,prefixes=prefix_count,sources=source_count)),flush=True)
    for row in s['rows']:
        ctx=next(c for c in old['contexts'] if c['run']==row['run']);expected=[str(Path('results/online_evidence_20261002/live')/row['run']/'packets'/(i+'.json')) for i in ctx['prefix_ids']]+[str(Path('results/streaming_recovery_20261002/study/source')/(row['run']+'_drive_%03d.json'%i)) for i in range(20,row['index']+1)]
        assert row['received_paths']==expected;assert row['scope']==ctx['anchor']['scope'] and row['motion']==ctx['anchor']['motion'];assert row['profile']==body.asdict(profiles[row['klass']])
        path=a.results/'study'/row['input_file'];assert sha(path)==row['input_sha256']
        if row['input_file'] not in cached_arrays:
            chunks=[]
            for f in expected:
                p,o,r=verified[f];chunks.append(np.column_stack([o[r[:,0]],r[:,1:]]));assert p['reference_us']<=row['ref_us']
            integers=np.unique(np.concatenate(chunks),axis=0);integers=integers[np.argsort(-integers[:,6],kind='stable')];times=np.unique(integers[:,6]);back=independent_back(times,row['ref_us']);perray=back[np.searchsorted(times,integers[:,6])]
            with np.load(path) as z:
                np.testing.assert_array_equal(z['integers'],integers);np.testing.assert_allclose(z['rays'][:,:6],integers[:,:6]*.001,rtol=0,atol=0);np.testing.assert_allclose(z['rays'][:,6],perray,rtol=0,atol=1e-12)
                segments=z['rays'][:,:6].copy()
            cached_arrays[row['input_file']]=(integers,times,back,perray,segments)
        integers,times,back,perray,segments=cached_arrays[row['input_file']]
        assert len(integers)==row['rays'] and times.tolist()==row['actual_times_us'];np.testing.assert_allclose(back,row['back_distances'],rtol=0,atol=1e-12)
        final=verified[expected[-1]][0];assert row['ref_us']==final['reference_us']
        oldrow=next(r for r in old['rows'] if r['run']==row['run'] and r['index']==row['index'] and r['method']=='fine_terminal' and r['preset']=='standard' and r['repeat']==0)
        assert row['lower_horizon_us']==oldrow['decision']['classes'][row['klass']]['horizon_us'] and row['joint_lower_horizon_us']==oldrow['horizon_us']
        error=math.sqrt(3)*(.01+.0005);assert row['error']==error
        assert math.isfinite(row['search_ms']) and row['search_ms']>=0 and row['candidates']==720*row['native_calls']
        w=row['witness'];summary={k:row[k] for k in ['run','index','klass','lower_horizon_us','joint_lower_horizon_us','rays']};summary['upper_horizon_us']=None if w is None else w['time_us']
        if w:
            h=Fraction(w['time_us'],1000000);assert 0<=h<=Fraction(3,2) and w['time_us']%5000==0
            u=np.asarray(w['outward_direction']);center=np.asarray(w['center_reference']);assert abs(np.linalg.norm(u)-1)<1e-14
            angle=w['direction_index']*math.pi/360+row['motion']['yaw'];np.testing.assert_allclose(u,[math.cos(angle),math.sin(angle)],rtol=0,atol=1e-14)
            raycenters=np.column_stack([center+perray[:,None]*u,np.full(len(segments),row['scope']['plane_z'])]);d=distances(raycenters,segments);clearance=float(d.min())-row['profile']['r_min']-error
            assert clearance>1e-8,(row['run'],row['index'],row['klass'],clearance);ray_checks+=len(d)
            # Each past interval has triangular speed 5 -> 5+3*dt/2 -> 5.
            for t0,t1 in zip(times,times[1:]):
                dt=Fraction(int(t1)-int(t0),1000000);peak=5+3*dt/2
                assert (peak-5)/(dt/2)==3 and (5-peak)/(dt/2)==-3
                assert (5+peak)*dt/2==5*dt+Fraction(3,4)*dt*dt
            age=Fraction(row['ref_us']-int(times[-1]),1000000);vref=5+3*age;forward=float(vref*h+Fraction(3,2)*h*h);future=center-u*forward
            c,sin=math.cos(row['motion']['yaw']),math.sin(row['motion']['yaw']);relative=future-np.asarray(row['scope']['query']);local=np.array([relative[0]*c+relative[1]*sin,-relative[0]*sin+relative[1]*c]);distance=float(np.linalg.norm(np.maximum(np.abs(local)-[2.3,1.3],0)))
            assert distance<row['profile']['r_min']-1e-7;assert w['time_us']>=row['lower_horizon_us'];assert row['profile']['r_min']<=row['profile']['r_max']
            summary.update(robust_ray_margin_m=round(clearance,6),rectangle_penetration_m=round(row['profile']['r_min']-distance,6),gap_us=w['time_us']-row['lower_horizon_us'])
        summaries.append(summary)
    forbidden={'search','flow','compact','observer','dictionary'};assert not(forbidden&set(sys.modules)),forbidden&set(sys.modules)
    out=dict(prefix_checks=prefix_count,source_checks=source_count,cases=36,witnesses=sum(r['upper_horizon_us'] is not None for r in summaries),independent_segment_checks=ray_checks,within_200ms=sum(r['upper_horizon_us'] is not None and r['upper_horizon_us']<=200000 for r in summaries),summaries=summaries,analyzer_sha256=sha(Path(__file__)),scope='Conditional ray-consistent kinematic witnesses; rigorous bounds within stated observation/motion/core model, finite-family failures censored; no real road or actual CARLA counterfactual guarantee.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['summaries','scope']}))
if __name__=='__main__':main()
