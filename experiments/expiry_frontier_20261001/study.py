#!/usr/bin/env python3
"""Finite source-backed post-analysis frontier study. Does not drive CARLA."""
import argparse, gzip, hashlib, json, math, socket, sys, time
from pathlib import Path
import numpy as np
from frontier import body, frontier, root_ready
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evidence_loop_20261001'))
from fast_path import Receiver


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
    a.out.mkdir(exist_ok=False)
    profiles = dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),
                    vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
    contract = body.Contract(); rows=[]; startup=[]; checks=0; packet_checks=0
    for f in sorted(a.capture.glob('*/record.json.gz')):
        record = json.loads(gzip.decompress(f.read_bytes()))
        rx = Receiver(profiles, contract, record['run'], 'Carla/Maps/Town10HD_Opt')
        last_root = None
        for d in record['decisions']:
            cloud_path=f.parent/'clouds'/(d['id']+'.npz'); cl = np.load(cloud_path)
            scope = body.Scope(record['run'], 'Carla/Maps/Town10HD_Opt', tuple(d['query']), float(cl['plane_z']))
            motion = body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            prior = rx.latest_region()
            if prior and not (prior.established <= d['stamp'] and math.ceil(d['stamp']*1e6) < rx._deadlines[prior.identity]):
                prior = None
            assert (prior.identity if prior else None) == d['prior']
            blob = (f.parent/'packets'/(d['id']+'.json')).read_bytes() if d['geometry'] else None
            if d['phase']=='warm' and d['index']==0:
                p=json.loads(last_root['blob'])['raw']['payload']
                startup.append(dict(run=record['run'], old_ready=last_root['d']['root_ready'],
                    integer_ready=root_ready(p['reference_us'],p['horizon_us'],last_root['d']['now']),
                    parent_expiry_us=p['reference_us']+p['horizon_us'],
                    first_warm_reference_us=math.ceil(d['stamp']*1e6),
                    valid_prior=prior is not None,
                    parent_remaining_at_root_ms=1000*((p['reference_us']+p['horizon_us'])/1e6-last_root['d']['now'])))
            if d['phase']=='root' or (d['phase'] in ['warm','drive'] and d['index']==0):
                o,r,ref=body.encode_source(cl['xyz'],cl['origin'],d['stamp'],d['stamp'])
                alternatives=[('all_observed_rays',o,r)]
                if blob:
                    _,po,pr=body.decode(body.canonical(json.loads(blob)['raw']),profiles,scope,contract)
                    alternatives.append(('transmitted_subset',po,pr))
                for label,origins,rays in alternatives:
                    t=time.perf_counter(); results=body.projections(origins,rays,ref,profiles,scope,contract)
                    answer=frontier(results,profiles,scope,motion,prior,ref/1e6); elapsed=time.perf_counter()-t
                    horizons=set(range(100_000,2_000_001,100_000))
                    h=answer['horizon_us']; horizons.update([max(1,h),min(2_000_000,h+1)])
                    for h_us in sorted(horizons):
                        ok=all(body.coverage(results[n],p,scope,motion,h_us/1e6,prior,ref/1e6)[0] for n,p in profiles.items())
                        assert ok == (0<h_us<=h), (record['run'],d['id'],label,h_us,answer)
                        checks+=1
                    verified_h=None
                    if label=='transmitted_subset' and h:
                        packet=json.loads(blob); payload=packet['raw']['payload']; payload['horizon_us']=h
                        packet['raw']['sha256']=hashlib.sha256(body.canonical(payload)).hexdigest()
                        extended=body.canonical(packet)
                        assert body.verify(extended,profiles,scope,contract,motion,prior,ref/1e6,0)
                        packet_checks+=1; verified_h=h
                        (a.out/(record['run']+'_'+d['id']+'_frontier.json')).write_bytes(extended)
                    age=d['now']-d['stamp']
                    row=dict(run=record['run'],id=d['id'],phase=d['phase'],method=record['method'],layout=record['layout'],
                        input_sha256=hashlib.sha256(cloud_path.read_bytes()).hexdigest(),kind=label,ray_count=len(rays),
                        frontier=answer,frontier_compute_ms=elapsed*1000,archived_age_ms=age*1000,
                        offline_slack_ms=h/1000-age*1000-200,
                        offline_slack_with_frontier_cost_ms=h/1000-age*1000-200-elapsed*1000,
                        verified_packet_horizon_us=verified_h)
                    rows.append(row);print(json.dumps(row),flush=True)
            if d['receiver_accepted']:
                assert rx.accept(blob,scope,motion,d['receiver_check_time'])
            if d['phase']=='root' and d['root_ready']:
                last_root=dict(d=d,blob=blob)
    root=Path(__file__).resolve().parents[2]
    deps={}
    for mod in list(sys.modules.values()):
        file=getattr(mod,'__file__',None)
        if file:
            path=Path(file).resolve()
            if path.is_file() and root in path.parents and path.suffix=='.py':
                deps[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(host=socket.gethostname(),rows=rows,startup=startup,reference_checks=checks,
        fully_verified_packets=packet_checks,source_sha256=deps,
        protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
        scope='Post-analysis fixed-region geometry frontier on actual saved observations; not fresh control or statistical safety.',validation='passed')
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
