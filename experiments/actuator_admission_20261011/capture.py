"""Finite actual ego feedback with moving walker; no policy certificate transfer."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import queue
import time
import traceback
from pathlib import Path
import numpy as np
import model as M
R=M.R

E = Path(__file__).resolve().parent
P = R.ROOT/'results'/E.name
DTYPE = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('cos', '<f4'), ('id', '<u4'), ('tag', '<u4')])


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def check():
    frozen = json.loads((E/'freeze.json').read_bytes())
    for part in ('sources', 'inputs'):
        for filename, digest in frozen[part].items():
            assert R.sha(R.ROOT/filename) == digest, filename


def matched(q, frame):
    while True:
        data = q.get(timeout=20)
        if data.frame == frame:
            return data
        assert data.frame < frame


def walker_speed(step):
    if step < 10:
        return 1.2*(step+1)/10
    if step < 90:
        return 1.2
    if step < 100:
        return 1.2*(99-step)/10
    return 0.


def main():
    import carla
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check()
    args.out.mkdir(parents=True, exist_ok=False)
    for sub in ('clouds', 'packets', 'episodes'):
        (args.out/sub).mkdir()
    context = json.loads((E/'context.json').read_bytes())
    background = json.loads((R.ROOT/'results/background_frontend_20261004/background.json').read_bytes())
    plan = json.loads((E/'plan.json').read_bytes())
    write(args.out/'plan.json', plan)
    write(args.out/'context.json', context)
    spec = importlib.util.spec_from_file_location('closed_ego_sample', R.ROOT/'experiments/ego_actuator_realization_20261004/capture.py')
    sampling = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampling)
    client = carla.Client('100.109.48.32', 2000)
    client.set_timeout(30)
    world = client.get_world()
    assert client.get_client_version() == client.get_server_version() == '0.9.15'
    assert world.get_map().name.endswith('Town10HD_Opt')
    assert not any(a.type_id.startswith(('vehicle.', 'walker.', 'sensor.')) for a in world.get_actors())
    original, weather = world.get_settings(), world.get_weather()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = .05
    settings.substepping = True
    settings.max_substep_delta_time = .01
    settings.max_substeps = 10
    world.apply_settings(settings)
    world.set_weather(carla.WeatherParameters.ClearNoon)
    owned, outcomes = [], []
    sensor = None
    anchor, road = np.asarray(context['basis']['anchor']), np.asarray(context['basis']['road'])
    yaw = math.degrees(math.atan2(road[1, 0], road[0, 0]))
    begin = time.perf_counter()
    try:
        library = world.get_blueprint_library()
        for request in plan:
            events, sources, rows = [], [], []
            record = dict(request=request, sources=sources, rows=rows, collisions=events)
            outcome = dict(id=request['id'], status='failed')
            try:
                pos = anchor+road@np.array([request['target_x_m'], request['initial_y_m'], .3])
                target = world.try_spawn_actor(library.find(context['blueprint']), carla.Transform(carla.Location(*map(float, pos)), carla.Rotation(yaw=yaw)))
                assert target is not None
                owned.append(target)
                assert sampling.vec(target.bounding_box.extent) == context['extent']
                target.apply_control(carla.WalkerControl(speed=0.))
                pos = anchor+road@np.array([-8., 0., .5])
                ego = world.try_spawn_actor(library.find('vehicle.audi.a2'), carla.Transform(carla.Location(*map(float, pos)), carla.Rotation(yaw=yaw)))
                assert ego is not None
                owned.append(ego)
                collision = world.spawn_actor(library.find('sensor.other.collision'), carla.Transform(), attach_to=ego)
                owned.append(collision)
                collision.listen(lambda event: events.append(dict(frame=event.frame, other=event.other_actor.type_id)))
                body = dict(extent=sampling.vec(ego.bounding_box.extent), offset=sampling.vec(ego.bounding_box.location), rotation=[ego.bounding_box.rotation.pitch, ego.bounding_box.rotation.yaw, ego.bounding_box.rotation.roll])
                assert body['rotation'] == [0., 0., 0.]
                assert R.A.pose.enclosing_radius_um(body['extent']) <= 2250000
                assert R.A.pose.enclosing_radius_um(body['extent'])+260000 <= R.RADIUS
                def command(throttle, brake):
                    start = time.perf_counter_ns()
                    control = carla.VehicleControl(throttle=throttle, brake=brake, steer=0., manual_gear_shift=True, gear=1)
                    responses = client.apply_batch_sync([carla.command.ApplyVehicleControl(ego.id, control)], False)
                    assert not any(response.error for response in responses)
                    return (time.perf_counter_ns()-start+999)//1000
                for _ in range(40):
                    command(0., 1.)
                    world.tick(20)
                attrs = dict(channels='256', range='35', points_per_second='2000000', rotation_frequency='20', upper_fov='10', lower_fov='-90', sensor_tick='0')
                bp = library.find('sensor.lidar.ray_cast_semantic')
                for key, value in attrs.items():
                    bp.set_attribute(key, value)
                sensor = world.spawn_actor(bp, carla.Transform(carla.Location(*map(float, anchor+road@np.array([0., 4., 8.])))))
                owned.append(sensor)
                q = queue.Queue()
                sensor.listen(q.put)
                for _ in range(3):
                    start = time.perf_counter_ns()
                    frame = world.tick(20)
                    data = matched(q, frame)
                    acquisition = (time.perf_counter_ns()-start+999)//1000
                record.update(body=body, target_id=target.id, ego_id=ego.id, sensor_attributes=attrs)
                history, pending, cache = [], [], None
                decoded_pending, control_pending, controls, control_decoded = [], [], [], []
                source_cpu_free=receiver_cpu_free=controller_cpu_free=control_tx_free=actuator_decode_free=0
                active_lease=None
                context_hash=hashlib.sha256(R.canonical(context)).hexdigest()
                body_radius=R.A.pose.enclosing_radius_um(body['extent'])
                record['controls']=controls
                record['clock']=dict(kind='exact per-episode 50ms plant frame clock; not wallclock',base_frame=frame,base_simulator_timestamp=world.get_snapshot().timestamp.elapsed_seconds)
                free, refused, reached = 0, False, False
                for step in range(630):
                    own = sampling.sample(world, ego, world.get_snapshot().frame)
                    frame = own['frame']
                    assert data.frame == frame
                    stamp=step*M.DT
                    if step==0:
                        record['clock'].update(base_frame=frame,base_simulator_timestamp=own['timestamp'])
                    assert frame==record['clock']['base_frame']+step
                    tr = target.get_transform()
                    truth = dict(center=sampling.vec(tr.transform(target.bounding_box.location)), velocity=sampling.vec(target.get_velocity()), rotation=[tr.rotation.pitch, tr.rotation.yaw, tr.rotation.roll])
                    if step < 600 and step % 2 == 0:
                        start = time.perf_counter_ns()
                        raw = np.frombuffer(data.raw_data, dtype=DTYPE)[::4].copy()
                        transform = np.asarray(data.transform.get_matrix())
                        copy_us = (time.perf_counter_ns()-start+999)//1000
                        start = time.perf_counter_ns()
                        wire, meta = R.encode(raw, transform, own, body, context, background, history, stamp, frame)
                        source_fee = (time.perf_counter_ns()-start+999)//1000+copy_us
                        name = request['id']+'_s%03d' % step
                        cloudpath, wirepath = args.out/'clouds'/(name+'.npz'), args.out/'packets'/(name+'.bin')
                        np.savez_compressed(cloudpath, raw=raw, transform=transform, timestamp=data.timestamp)
                        wirepath.write_bytes(wire)
                        source_cpu_free=M.service(stamp+M.SENSING,source_cpu_free,source_fee)
                        free,arrival=M.transmit(source_cpu_free,free,len(wire))
                        item = dict(step=step, frame=frame, source_us=stamp, acquisition_model_us=M.SENSING, render_acquisition_wall_us=acquisition, source_fee_us=source_fee, source_ready_us=source_cpu_free, cloud=cloudpath.name, cloud_sha256=R.sha(cloudpath), packet=wirepath.name, packet_sha256=R.sha(wirepath), wire_bytes=len(wire), arrival_us=arrival, tx_free_us=free, meta=meta, target_returns_audit_only=int((raw['id'] == target.id).sum()))
                        sources.append(item)
                        pending.append((item, wire))
                    receiver_fee = 0
                    delivered = []
                    while pending and pending[0][0]['arrival_us'] <= stamp:
                        item, wire = pending.pop(0)
                        start = time.perf_counter_ns()
                        decoded = R.decode(wire, context)
                        fee = (time.perf_counter_ns()-start+999)//1000
                        receiver_fee += fee
                        receiver_cpu_free=M.service(item['arrival_us'],receiver_cpu_free,fee)
                        item.update(receiver_ready_us=receiver_cpu_free,receiver_fee_us=fee)
                        decoded_pending.append((receiver_cpu_free,decoded,item['step']))
                    while decoded_pending and decoded_pending[0][0]<=stamp:
                        ready,cache,source_step=decoded_pending.pop(0)
                        delivered.append(source_step)
                    query = R.own_position(own, context['basis'])
                    speed = math.hypot(*own['velocity'][:2])
                    domain = speed <= .75 and -10000000 <= query[0] <= 6000000 and abs(query[1]) <= 500000
                    refused = refused or not domain or bool(events)
                    reached = reached or (query[0] >= 3000000 and abs(query[1]) <= 500000)
                    query_fee=0
                    if cache is not None and step<600 and not refused and not reached:
                        start=time.perf_counter_ns()
                        lease=M.proposal(cache,query,context,request['id'],step,stamp,request['method'])
                        lease_wire=M.pack(lease)
                        query_fee=(time.perf_counter_ns()-start+999)//1000
                        controller_cpu_free=M.service(stamp,controller_cpu_free,query_fee)
                        control_tx_free,arrival=M.transmit(controller_cpu_free,control_tx_free,len(lease_wire))
                        path=args.out/'packets'/(request['id']+'_q%03d.bin'%step)
                        path.write_bytes(lease_wire)
                        control=dict(step=step,query_us=stamp,lease=lease,query_fee_us=query_fee,
                            controller_ready_us=controller_cpu_free,wire_bytes=len(lease_wire),
                            tx_free_us=control_tx_free,arrival_us=arrival,packet=path.name,packet_sha256=R.sha(path))
                        controls.append(control)
                        control_pending.append((control,lease_wire))
                    while control_pending and control_pending[0][0]['arrival_us']<=stamp:
                        control,wire=control_pending.pop(0)
                        start=time.perf_counter_ns()
                        lease=M.unpack(wire)
                        fee=(time.perf_counter_ns()-start+999)//1000
                        actuator_decode_free=M.service(control['arrival_us'],actuator_decode_free,fee)
                        control.update(decode_fee_us=fee,decode_ready_us=actuator_decode_free)
                        control_decoded.append((actuator_decode_free,lease))
                    while control_decoded and control_decoded[0][0]<=stamp:
                        ready,active_lease=control_decoded.pop(0)
                    start=time.perf_counter_ns()
                    gate=M.admit(active_lease,stamp,query,body_radius,request['id'],context_hash)
                    admission_fee=(time.perf_counter_ns()-start+999)//1000
                    go=step<600 and not refused and not reached and gate['allowed']
                    throttle, brake = R.relay(own, go)
                    assert world.get_snapshot().frame==frame
                    command_fee = command(throttle, brake)
                    assert world.get_snapshot().frame==frame
                    speed_target = 0. if request['motion'] == 'clear_stay' else walker_speed(step)
                    direction = road@np.array([0., request['direction_y'], 0.])
                    target.apply_control(carla.WalkerControl(direction=carla.Vector3D(*map(float, direction)), speed=speed_target, jump=False))
                    start = time.perf_counter_ns()
                    next_frame = world.tick(20)
                    data = matched(q, next_frame)
                    acquisition = (time.perf_counter_ns()-start+999)//1000
                    after = sampling.sample(world, ego, next_frame)
                    refused = refused or math.hypot(*after['velocity'][:2]) > .75
                    rows.append(dict(step=step, now_us=stamp, decision_us=stamp, own=own, after=after,
                        truth=truth, query_um=query, gate=gate, receiver_fee_us=receiver_fee, query_fee_us=query_fee,
                        command_fee_us=command_fee, admission_wall_fee_us=admission_fee, active_lease=active_lease, domain_ok=domain,
                        episode_refused=refused, reached=reached, engineering_go=bool(go), requested_throttle=throttle,
                        requested_brake=brake, target_requested_speed_audit_only=speed_target, delivered=delivered))
                outcome['status'] = 'captured'
                record['pending_at_end']=dict(sources=[item['step'] for item,wire in pending],
                    decoded_sources=[s for ready,obj,s in decoded_pending],
                    controls=[item['step'] for item,wire in control_pending],
                    decoded_controls=[lease['seq'] for ready,lease in control_decoded])
            except Exception:
                record['exception'] = traceback.format_exc()
                outcome['reason'] = 'capture_exception'
            finally:
                if sensor is not None:
                    sensor.stop()
                    sensor = None
                for actor in reversed(owned):
                    if actor.type_id.startswith('sensor.'):
                        actor.stop()
                    actor.destroy()
                owned = []
                world.tick(20)
            record['outcome'] = dict(outcome)
            logical = (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
            path = args.out/'episodes'/(request['id']+'.json.gz')
            path.write_bytes(gzip.compress(logical, mtime=0))
            outcome.update(file=str(path.relative_to(args.out)), sha256=R.sha(path), logical_sha256=hashlib.sha256(logical).hexdigest(), rows=len(rows), sources=len(sources))
            outcomes.append(outcome)
            write(args.out/'outcomes.json', outcomes)
            print(json.dumps(dict(outcome, elapsed_s=time.perf_counter()-begin)), flush=True)
        write(args.out/'manifest.json', dict(planned=len(plan), captured=sum(v['status']=='captured' for v in outcomes), freeze_sha256=R.sha(E/'freeze.json'), elapsed_s=time.perf_counter()-begin, scope='actual ego physics with defined virtual CPU/radio queues and atomic plant-boundary actuator; not wallclock realtime, hardware watchdog, or risk certificate', goal_complete=False))
    finally:
        if sensor is not None:
            sensor.stop()
        for actor in reversed(owned):
            actor.destroy()
        if world.get_settings().synchronous_mode:
            world.tick(20)
        world.apply_settings(original)
        world.set_weather(weather)
        write(args.out/'cleanup.json', dict(vehicles=len(world.get_actors().filter('vehicle.*')), walkers=len(world.get_actors().filter('walker.*')), sensors=len(world.get_actors().filter('sensor.*')), synchronous=world.get_settings().synchronous_mode))


if __name__ == '__main__':
    main()
