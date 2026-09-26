"""Open-loop static route probes on existing frozen detector outputs.

This is NOT a planner benchmark or collision-rate experiment. GT is evaluation-only.
The exact selector knows its own sender observations plus a paid receiver request.
"""
import argparse
import hashlib
import itertools
import json
import platform
import struct
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union

from run_bayes_probe import greedy, pairwise


PACKET = struct.Struct('!II8eeH')


def encode_box(frame, obj, corners, confidence):
    body = PACKET.pack(frame, obj, *np.asarray(corners[:4, :2]).reshape(-1), confidence, 1)
    raw = body + struct.pack('!I', zlib.crc32(body))
    return raw


def decode_box(raw):
    body, check = raw[:-4], raw[-4:]
    if zlib.crc32(body) != struct.unpack('!I', check)[0]:
        raise ValueError('CRC mismatch')
    vals = PACKET.unpack(body)
    return np.array(vals[2:10]).reshape(4, 2), vals[10]


def request_packet(frame, path, local_scores):
    body = struct.pack('!IHH', frame, len(path), len(local_scores))
    body += np.asarray(path, dtype='>f2').tobytes()
    body += np.asarray(local_scores, dtype='>f2').tobytes()
    return body + struct.pack('!I', zlib.crc32(body))


def request_decode(raw):
    body = raw[:-4]
    if zlib.crc32(body) != struct.unpack('!I', raw[-4:])[0]:
        raise ValueError('request CRC mismatch')
    _, n, k = struct.unpack('!IHH', body[:8])
    arr = np.frombuffer(body[8:], dtype='>f2').astype(float)
    assert len(arr) == 2*n+k
    return arr[:2*n].reshape(n,2), arr[2*n:]


def scene_index(root):
    frames, start = {}, 0
    for scene_id, scene in enumerate(sorted(p for p in root.iterdir() if p.is_dir())):
        cavs = sorted(p for p in scene.iterdir() if p.is_dir())
        if int(cavs[0].name) < 0:
            cavs = cavs[1:]+cavs[:1]
        paths = sorted(p for p in cavs[0].glob('*.yaml') if 'additional' not in p.name)
        for i, p in enumerate(paths):
            frames[f'{scene_id:02d}_{start+i:06d}'] = (scene.name, p)
        start += len(paths)
    return frames


def read_route(path):
    # Read plain YAML through SafeLoader; no construction of Python objects.
    obj = yaml.safe_load(path.read_text())
    pose = np.array(obj['lidar_pose'])
    plan = np.asarray(obj.get('plan_trajectory', []), dtype=float)
    if plan.ndim != 2 or len(plan) < 1 or plan.shape[1] < 2:
        raise ValueError('missing_or_empty_recorded_route')
    xy = plan[:, :2]-pose[:2]
    yaw = np.deg2rad(pose[4])
    rot = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    xy = xy @ rot  # row-vector inverse yaw; small pitch/roll deliberately ignored
    xy = np.vstack([np.zeros(2), xy])
    xy = xy[np.r_[True, np.linalg.norm(np.diff(xy,axis=0),axis=1) > 1e-3]]
    if len(xy) < 2 or np.linalg.norm(np.diff(xy,axis=0),axis=1).sum() < 1:
        raise ValueError('recorded_route_shorter_than_1m')
    return xy, float(obj['ego_speed']), abs(float(pose[3])), abs(float(pose[5]))


def make_actions(route, family):
    line = LineString(route)
    length = float(line.length)
    if length < 1:
        raise ValueError('route shorter than 1m')
    specs = [(0, 0), (.35, 0), (.65, 0), (1, 0)]
    if family == 'lateral_stress':
        specs += [(1, -3.5), (1, 3.5)]
    shapes, base, progress = [None], [1.0], [0.0]
    for fraction, lateral in specs[1:]:
        dist = np.linspace(0, length*fraction, 24)
        points = np.array([line.interpolate(float(s)).coords[0] for s in dist])
        tangent = np.gradient(points, axis=0)
        tangent /= np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True), 1e-9)
        normal = np.c_[-tangent[:,1], tangent[:,0]]
        # Lateral candidates are a stress test, not certified drivable trajectories.
        points += normal*(lateral*np.minimum(dist/8.0,1.0))[:,None]
        footprints = []
        for point, forward, side in zip(points,tangent,normal):
            footprints.append(Polygon([point+sx*2.25*forward+sy*1.0*side
                                       for sx,sy in [(1,1),(1,-1),(-1,-1),(-1,1)]]))
        shapes.append(unary_union(footprints))
        base.append(1-fraction+.08*abs(lateral)/3.5)
        progress.append(fraction)
    return shapes, np.array(base), np.array(progress)


def impacts(boxes, scores, shapes):
    answer = np.zeros((len(boxes),len(shapes)))
    for i, (box, score) in enumerate(zip(boxes,scores)):
        poly = Polygon(box[:4,:2]).convex_hull
        if poly.is_empty or poly.area < 1e-5:
            continue
        for a, shape in enumerate(shapes[1:],1):
            if poly.intersects(shape):
                answer[i,a] = score
    return answer


def nonself_mask(boxes):
    """Pose-only self suppression, applied independently to predictions and GT.

    The sender observes ego itself. Cache's merged GT contains ego as well.
    Require both center within 1.5m of known ego origin and footprint covering
    that origin. This is a declared heuristic, never GT association.
    """
    origin = Point(0,0)
    return np.array([not (np.linalg.norm(box[:4,:2].mean(axis=0)) < 1.5
                         and Polygon(box[:4,:2]).convex_hull.covers(origin))
                     for box in boxes],dtype=bool)


def subset_tables(ego_risk, message_risk, base):
    n = len(message_risk)
    risks = np.broadcast_to(ego_risk,(1 << n,len(base))).copy()
    for m in range(1,1 << n):
        bit = m & -m
        risks[m] = np.maximum(risks[m ^ bit],message_risk[bit.bit_length()-1])
    costs = base[None,:]+100*(risks >= .3)
    action = costs.argmin(axis=1)
    reference = costs[-1]
    regret = reference[action]-reference.min()
    assert np.all(regret >= -1e-9)
    return action, regret, reference


def delivery_expectation(values, n, q, rho=0):
    """Subset-erasure transform; rho mixture of independent and common events."""
    result = np.array(values, dtype=float, copy=True)
    for i in range(n):
        masks = np.arange(1 << n)
        selected = masks[(masks & (1 << i)) != 0]
        result[selected] = q*result[selected]+(1-q)*result[selected ^ (1 << i)]
    common = q*np.asarray(values)+(1-q)*values[0]
    return (1-rho)*result+rho*common


def select(method, utility, k, tie, confidence):
    n = len(tie)
    k = min(k,n)
    if method == 'ego':
        return 0
    if method == 'confidence_broadcast':
        return sum(1 << int(i) for i in np.argsort(-confidence,kind='stable')[:k])
    if method == 'coverage_ranking':
        return sum(1 << int(i) for i in np.argsort(-tie,kind='stable')[:k])
    if method == 'greedy_voi':
        return greedy(utility,k,tie)
    if method == 'pair_lookahead':
        return pairwise(utility,k,tie)
    if method == 'exact_subset':
        return max((m for m in range(1 << n) if m.bit_count() <= k),
                   key=lambda m: (round(utility[m],10),-m.bit_count(),-m))
    raise ValueError(method)


def configurations():
    answer = []
    # Keep loose configurations: savings cannot be inferred only under tiny budgets.
    for budget in [96,160,288,512]:
        for q in [1.0,.8]:
            answer.append(dict(name=f'b{budget}_q{q}',budget=budget,q=q,rho=0,
                               rate=100_000,deadline_ms=100,compute=True))
    for d in [10,30]:
        answer.append(dict(name=f'deadline{d}',budget=288,q=.8,rho=0,
                           rate=100_000,deadline_ms=d,compute=True))
    answer.append(dict(name='correlated',budget=160,q=.8,rho=.5,rate=100_000,
                       deadline_ms=100,compute=True))
    answer.append(dict(name='no_compute_charge',budget=160,q=.8,rho=0,rate=100_000,
                       deadline_ms=100,compute=False))
    answer.append(dict(name='fast_loose',budget=512,q=1.,rho=0,rate=1_000_000,
                       deadline_ms=100,compute=True))
    return answer


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache',default='/home/sheng/voi/data/opv2v')
    p.add_argument('--raw',default='/home/sheng/BEV_reproduction/data/OPV2V/opv2v_data_dumping/validate')
    p.add_argument('--output',required=True)
    p.add_argument('--limit',type=int,default=0)
    args = p.parse_args()
    out = Path(args.output);out.mkdir(parents=True,exist_ok=True)
    source = Path(args.cache)
    original = json.loads((source/'manifest.json').read_text())
    split = set(original['evaluation_scenes'])
    index = scene_index(Path(args.raw))
    documented = pd.read_csv(source/'frames.csv').set_index('frame')
    files = sorted(source.glob('*.npz'))
    if args.limit:files = files[:args.limit]
    configs = configurations()
    methods = ['ego','confidence_broadcast','coverage_ranking','greedy_voi','pair_lookahead','exact_subset']
    rows, diagnostics, files_manifest, exclusions = [], [], [], []
    begin = time.time()
    for j, file in enumerate(files):
        frame = file.stem
        scene, raw_yaml = index[frame]
        assert scene == documented.loc[frame,'scene']
        data = np.load(file,allow_pickle=False)
        files_manifest.append(dict(frame=frame,scene=scene,npz_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                                   yaml=str(raw_yaml),yaml_sha256=hashlib.sha256(raw_yaml.read_bytes()).hexdigest()))
        try:
            route, speed, roll, pitch = read_route(raw_yaml)
        except ValueError as error:
            exclusions.append(dict(frame=frame,scene=scene,reason=str(error)))
            continue
        # GT does not participate in message candidate filtering.
        ego_keep = nonself_mask(data['ego'])
        sender_keep = nonself_mask(data['sender'])
        sender_ids = np.flatnonzero(sender_keep)
        distances = np.linalg.norm(data['sender'][sender_ids].mean(axis=1)[:,:2],axis=1)
        ids = sender_ids[np.argsort(distances,kind='stable')[:8]]
        wire = [encode_box(j,int(i),data['sender'][i],float(data['sender_score'][i])) for i in ids]
        decoded = [decode_box(w) for w in wire]
        boxes = np.array([x[0] for x in decoded]).reshape(-1,4,2)
        confidence = np.array([x[1] for x in decoded])
        n = len(boxes)
        assert all(len(w) == 32 for w in wire)
        for family in ['route_prefix','lateral_stress']:
            started = time.perf_counter()
            quantized_route = route.astype(np.float16).astype(float)
            shapes, base, progress = make_actions(quantized_route,family)
            e = impacts(data['ego'][ego_keep],data['ego_score'][ego_keep],shapes)
            ego_risk = e.max(axis=0) if len(e) else np.zeros(len(base))
            request = request_packet(j,quantized_route,ego_risk)
            decoded_route, decoded_risk = request_decode(request)
            np.testing.assert_array_equal(decoded_route,quantized_route)
            message_risk = impacts(boxes,confidence,shapes)
            action, regret, ref = subset_tables(decoded_risk,message_risk,base)
            table_ms = (time.perf_counter()-started)*1000
            # Post-selection diagnostics can use GT; selectors never receive them.
            gt_keep = nonself_mask(data['gt'])
            gt_imp = impacts(data['gt'][gt_keep],np.ones(int(gt_keep.sum())),shapes)
            gt_blocked = gt_imp.max(axis=0) if len(gt_imp) else np.zeros(len(base))
            gt_cost = base+100*gt_blocked
            gt_regret = gt_cost[action]-gt_cost.min()
            hazard = gt_blocked[action]
            match = (action == action[-1]).astype(float)
            tie = (message_risk*(1.1-base)[None,:]).sum(axis=1)
            diagnostics.append(dict(frame=frame,scene=scene,split='evaluation' if scene in split else 'development',
                family=family,n=n,request_bytes=len(request),table_ms=table_ms,speed_kmh=speed,
                abs_roll=roll,abs_pitch=pitch,ego_regret=regret[0],full_action=int(action[-1]),
                removed_ego=int((~ego_keep).sum()),removed_sender=int((~sender_keep).sum()),
                removed_gt=int((~gt_keep).sum()),
                ego_action=int(action[0]),ego_gt_block=hazard[0],full_gt_block=hazard[-1],
                ego_progress=progress[action[0]],full_progress=progress[action[-1]],
                beneficial_singletons=int(sum(regret[1 << i] < regret[0]-1e-9 for i in range(n)))))
            for config in configs:
                expected = {name:delivery_expectation(values,n,config['q'],config['rho'])
                            for name,values in [('regret',regret),('gt_regret',gt_regret),
                                               ('gt_block',hazard),('match',match),('progress',progress[action])]}
                for method in methods:
                    needs_request = method not in ['ego','confidence_broadcast']
                    control = len(request) if needs_request else 0
                    # A request must arrive before sender can use receiver state.
                    request_success = config['q'] if needs_request else 1.
                    budget_k = max(0,(config['budget']-control)//32)
                    effective_ms = config['deadline_ms']-(table_ms if config['compute'] else 0)
                    link_bytes = max(0,int(effective_ms*config['rate']/8000)-control)
                    k = min(n,budget_k,link_bytes//32)
                    start = time.perf_counter()
                    chosen = select(method,-expected['regret'],k,tie,confidence)
                    select_ms = (time.perf_counter()-start)*1000
                    # Charge observed selector time; if needed, conservatively reselect.
                    if config['compute']:
                        link_bytes = max(0,int((effective_ms-select_ms)*config['rate']/8000)-control)
                        k2 = min(n,budget_k,link_bytes//32)
                        if k2 < k:
                            chosen = select(method,-expected['regret'],k2,tie,confidence)
                            k = k2
                    request_feasible = control <= config['budget'] and control*8000/config['rate'] <= max(0,effective_ms-select_ms)
                    if method == 'ego' or (needs_request and not request_feasible):
                        chosen = 0;control = 0;request_success = 0 if needs_request else 1
                    size = chosen.bit_count()*32
                    assert size+control <= config['budget']
                    r = dict(frame=frame,scene=scene,split='evaluation' if scene in split else 'development',
                        family=family,config=config['name'],method=method,n=n,capacity=k,mask=chosen,
                        control_bytes=control,data_bytes=size,planned_bytes=control+size,
                        expected_tx_bytes=control+request_success*size,
                        table_ms=table_ms,selector_ms=select_ms,
                        serialized_ms=(control+size)*8000/config['rate'])
                    for name, arr in expected.items():
                        r[name] = request_success*arr[chosen]+(1-request_success)*arr[0]
                    rows.append(r)
        if j % 40 == 0:print(f'OPV2V {j+1}/{len(files)} elapsed={time.time()-begin:.1f}s',flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out/'per_frame.csv',index=False)
    pd.DataFrame(diagnostics).to_csv(out/'diagnostics.csv',index=False)
    pd.DataFrame(exclusions,columns=['frame','scene','reason']).to_csv(out/'exclusions.csv',index=False)
    metrics = ['regret','gt_regret','gt_block','match','progress','planned_bytes','expected_tx_bytes','table_ms','selector_ms']
    df.groupby(['split','family','config','method'])[metrics].mean().to_csv(out/'summary.csv')
    (out/'input_manifest.json').write_text(json.dumps(files_manifest,indent=2))
    manifest = dict(host=platform.node(),arguments=vars(args),seconds=time.time()-begin,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(Path(__file__).with_name('run_bayes_probe.py').read_bytes()).hexdigest(),
        original_cache_manifest=original,configurations=configs,source_frames=len(files),
        eligible_frames=int(df.frame.nunique()),excluded_frames=len(exclusions),
        caveats=['OPV2V simulated validation data; frozen cached detections, not new GPU inference.',
                 'Static swept-box route probe; not dynamic planning or collision probability.',
                 'Lateral alternatives not verified against lanes/dynamics.',
                 'One sender, max 8 nearest objects; receiver state explicitly sent.',
                 'Pose-only self suppression: center <1.5m and footprint covers origin; no GT association.',
                 'Confidence threshold is a fixed heuristic, not calibrated risk.',
                 'Software erasure/constant service-rate model, not measured PC5.',
                 'Cached-probe construction and selector timing charged; sensor/network inference latency excluded.',
                 'Yaw-only path transform; pitch/roll recorded for audit.',
                 'Late unreceived messages ignored; no retransmissions or asynchronous expiry in v1.'])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Done {df.frame.nunique()}/{len(files)} eligible frames {len(rows)} rows; excluded={len(exclusions)}',flush=True)


if __name__ == '__main__':
    main()
