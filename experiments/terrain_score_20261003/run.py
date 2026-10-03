#!/usr/bin/env python3
import argparse,hashlib,json,sys,time
from pathlib import Path
from fractions import Fraction
import numpy as np
from model import score
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/pose_inversion_20261003'))
from bounds import rotation

def frac(x):return Fraction(x['numerator'],x['denominator'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--timings',required=True,type=Path);a=ap.parse_args();shape=ROOT/'results/shape_evidence_20261002';rows=[];timings=[];episodes=[];input_hashes={}
    for followup in (False,True):
        base=shape/'availability_followup' if followup else shape
        planpath=ROOT/'experiments/shape_evidence_20261002'/('availability_followup/plan.json' if followup else 'plan.json')
        plan=json.loads(planpath.read_bytes());plan=[p for p in plan if (p['blueprint'].startswith('walker.')==followup)];episodes+=plan
        records=json.loads((base/'capture/record.json').read_bytes());keep={p['id'] for p in plan}
        for path in [planpath,base/'capture/record.json']:input_hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        for rec in records:
            if rec['status']!='captured' or rec['episode']['id'] not in keep:continue
            path=base/'capture'/rec['cloud_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['cloud_sha256'];input_hashes[str(path.relative_to(ROOT))]=rec['cloud_sha256']
            with np.load(path) as z:points=np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']].astype(float)@z['transform'][:3,:3].T+z['origin'];origin=z['origin']
            rot=np.array(rec['actor_transform']['matrix'])[:3,:3]@rotation(*np.deg2rad(rec['bounding_box']['rotation']))
            for stride in (1,4,16):
                t=time.perf_counter_ns();s=score(points[::stride],origin,rec['center'],rot,rec['bounding_box']['extent']);timings.append(dict(id=rec['id'],stride=stride,ns=time.perf_counter_ns()-t));rows.append(dict(episode=rec['episode']['id'],id=rec['id'],blueprint=rec['blueprint'],stride=stride,score=s))
    byep={e['id']:[r for r in rows if r['episode']==e['id']] for e in episodes};summaries={};thresholds={}
    for bp in sorted({e['blueprint'] for e in episodes}):
        cal=[e for e in episodes if e['blueprint']==bp and e['split']=='calibration'];test=[e for e in episodes if e['blueprint']==bp and e['split']=='test'];assert len(cal)==19 and len(test)==20
        missing=[e['id'] for e in cal if len(byep[e['id']])!=6];q=max(max(frac(r['score']) for r in byep[e['id']]) if len(byep[e['id']])==6 else Fraction(0) for e in cal);thresholds[bp]=q
        bad=[e['id'] for e in test if len(byep[e['id']])==6 and any(frac(r['score'])>q for r in byep[e['id']])];refused=[e['id'] for e in test if len(byep[e['id']])!=6]
        summaries[bp]=dict(threshold=dict(numerator=q.numerator,denominator=q.denominator),calibration_missing=missing,test_refused=refused,test_false_exclusion=bad,available_test_episodes=20-len(refused),supported_test_frames=sum(r['score']['reason'] is None for e in test for r in byep[e['id']]))
    pose=ROOT/'results/pose_inversion_20261003';bank=json.loads((pose/'witness_bank_sheng.json').read_bytes());sources={s['case']:s for s in json.loads((pose/'replay/sources.json').read_bytes())};witnesses=[];clouds={}
    for c in bank['candidates']:
        source=sources[c['case']]
        if c['case'] not in clouds:
            with np.load(ROOT/source['source_cloud']) as z:clouds[c['case']]=(np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']].astype(float)@z['transform'][:3,:3].T+z['origin'],z['origin'].copy())
        points,origin=clouds[c['case']];p=np.array(c['pose']);center=np.array(source['anchor'])+np.array(source['road_rotation'])@p[:3];ss={str(s):score(points[::s],origin,center,rotation(*p[3:]),source['extent']) for s in (16,4,1)};q=thresholds[source['blueprint']]
        witnesses.append(dict(case=c['case'],query_index=c['query_index'],pose=c['pose'],upper_us=c['upper_us'],old_accepted_by_stride=c['accepted_by_stride'],scores=ss,accepted_by_stride={str(s):all(frac(ss[str(t)])<=q for t in (16,4,1) if t>=s) for s in (16,4,1)}))
    out=dict(summary=summaries,rows=rows,witnesses=witnesses,input_hashes=input_hashes,source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*')) if p.name in ('model.py','run.py','PROTOCOL.md')},scope='Retrospective fixed model repair, no fresh independent validation or positive TTL claim.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');a.timings.write_text(json.dumps(timings,indent=2)+'\n');print(json.dumps(dict(summary=summaries,surviving_by_stride={str(s):sum(c['accepted_by_stride'][str(s)] for c in witnesses) for s in (16,4,1)}),indent=2))
if __name__=='__main__':main()
