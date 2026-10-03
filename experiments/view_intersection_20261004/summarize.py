#!/usr/bin/env python3
import argparse,hashlib,json,statistics
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def stats(v):
    v=sorted(v)
    return dict(n=len(v),median_us=statistics.median(v) if v else None,p95_us=v[max(0,(95*len(v)+99)//100-1)] if v else None,max_us=max(v) if v else None)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=read(a.results/'analysis_sheng.json');audit=read(a.results/'audit_sheng.json');assert audit['analysis_sha256']==sha(a.results/'analysis_sheng.json');parent=read(a.parent/'summary_sheng.json');bps=[c['blueprint'] for c in parent['classes']];comparisons=[]
    for rate in (20000000,2000000):
        for method in ('union','lossless_centers','full_xyz'):
            rows=[t for t in audit['trace_checks'] if t['bitrate']==rate and t['method']==method];assert len(rows)==360
            costs=[j['extra_us'] for t in d['traces'] if t['bitrate']==rate and t['method']==method for j in t['jobs']]
            comparisons.append(dict(bitrate=rate,method=method,scheduled_queries=11520,grants=sum(t['grants'] for t in rows),primary_grants=sum(t['primary_grants'] for t in rows),intersection_chosen_grants=sum(t['intersection_chosen_grants'] for t in rows),grants_on_parent_excluded_episodes=sum(t['grants_on_parent_excluded_episode'] for t in rows),observed_occupied_grid_grants=sum(t['observed_occupied_grid_grants'] for t in rows),contradiction_events=sum(t['contradictions'] for t in rows),extra_receiver_cost=stats(costs),classes=[dict(blueprint=bp,grants=sum(t['grants'] for t in rows if t['blueprint']==bp),primary_grants=sum(t['primary_grants'] for t in rows if t['blueprint']==bp),intersection_chosen_grants=sum(t['intersection_chosen_grants'] for t in rows if t['blueprint']==bp)) for bp in bps]))
    pairs=audit['pair_checks'];gains=[v for c in pairs for v in c['horizon_gains_us']];distance_gaps=[z['distance']['upper_um']-z['distance']['lower_um'] for p in d['pairs'].values() for z in p['geometry']['queries']];age_gaps=[z['upper_us']-z['lower_us'] for p in d['pairs'].values() for z in p['geometry']['queries']]
    result=dict(total=dict(captured_test_pairs=len(pairs),planned_test_pairs=1080,planned_test_episodes=360,status_counts={s:sum(c['status']==s for c in pairs) for s in ('bounded','empty','precision_gap','missing_view')},certificate_checks=audit['certificate_checks'],computed_horizon_queries=len(gains),geometric_gains_greater_than_1us=sum(v>1 for v in gains),geometric_horizon_gain=stats(gains),maximum_distance_bracket_um=max(distance_gaps,default=0),maximum_expiry_bracket_us=max(age_gaps,default=0),parent_test_excluded_episodes=parent['total']['test_excluded_episodes'],inherited_joint_calibration_confidence_lower=parent['total']['joint_calibration_confidence_lower']),comparisons=comparisons,source_sha256=sha(Path(__file__)),analysis_sha256=sha(a.results/'analysis_sheng.json'),audit_sha256=sha(a.results/'audit_sheng.json'),parent_summary_sha256=sha(a.parent/'summary_sheng.json'),scope='Paid finite post-result intersection development. Geometry maximality only within declared calibrated supports/motion. Inherited current-state coverage failures retained; no new holdout or raw/physical/novelty claim.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['total']))
if __name__=='__main__':main()
