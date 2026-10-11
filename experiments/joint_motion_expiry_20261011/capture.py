"""Finite dynamic sensing development batch. Truth is recorded for audit only."""
import argparse
import gzip
import hashlib
import json
import math
import queue
import time
import traceback
from pathlib import Path
import numpy as np

E = Path(__file__).resolve().parent
ROOT = E.parents[1]
DTYPE = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                  ('cos', '<f4'), ('id', '<u4'), ('tag', '<u4')])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def check():
    freeze = json.loads((E/'freeze.json').read_bytes())
    for part in ('sources', 'inputs'):
        for path, digest in freeze[part].items():
            assert sha(ROOT/path) == digest, path


def matched(q, frame):
    while True:
        d = q.get(timeout=20)
        if d.frame == frame:
            return d
        assert d.frame < frame


def main():
    import carla
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    check()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'clouds').mkdir()
    (args.out/'episodes').mkdir()
    ctx = json.loads((E/'context.json').read_bytes())
    plan = json.loads((E/'plan.json').read_bytes())
    dump(args.out/'context.json', ctx)
    dump(args.out/'plan.json', plan)
    client = carla.Client('100.109.48.32', 2000)
    client.set_timeout(30)
    assert client.get_client_version() == client.get_server_version() == '0.9.15'
    world = client.get_world()
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
    outcomes = []
    owned = []
    sensor = None
    anchor, road = np.asarray(ctx['basis']['anchor']), np.asarray(ctx['basis']['road'])
    yaw = math.degrees(math.atan2(road[1, 0], road[0, 0]))
    attrs = dict(channels='256', range='35', points_per_second='2000000',
                 rotation_frequency='20', upper_fov='10', lower_fov='-90', sensor_tick='0')
    begin = time.perf_counter()
    try:
        lib = world.get_blueprint_library()
        for request in plan:
            record = dict(request=request, rows=[], sources=[])
            outcome = dict(id=request['id'], status='failed')
            try:
                direction = np.asarray(request['direction'], dtype=float)
                warm_displacement = direction*request['speed_mps']
                local = np.array([request['reference_x_m'], request['reference_y_m'], .05])-warm_displacement
                pos = anchor+road@local
                target = world.try_spawn_actor(lib.find(ctx['blueprint']), carla.Transform(
                    carla.Location(*map(float, pos)), carla.Rotation(yaw=yaw)))
                assert target is not None
                owned.append(target)
                assert vec(target.bounding_box.extent) == ctx['extent']
                control = carla.WalkerControl(direction=carla.Vector3D(*map(float, road@direction)),
                                              speed=request['speed_mps'], jump=False)
                target.apply_control(control)
                for _ in range(20):
                    world.tick(20)
                bp = lib.find('sensor.lidar.ray_cast_semantic')
                for k, v in attrs.items():
                    bp.set_attribute(k, v)
                sensor = world.spawn_actor(bp, carla.Transform(carla.Location(*map(float, anchor+road@np.array([0., 4., 8.])))))
                owned.append(sensor)
                q = queue.Queue()
                sensor.listen(q.put)
                record.update(target_id=target.id, sensor_attributes=attrs,
                              extent=vec(target.bounding_box.extent),
                              offset=vec(target.bounding_box.location),
                              body_rotation=[target.bounding_box.rotation.pitch,
                                             target.bounding_box.rotation.yaw,
                                             target.bounding_box.rotation.roll])
                for step in range(60):
                    start = time.perf_counter_ns()
                    frame = world.tick(20)
                    d = matched(q, frame)
                    acquisition = (time.perf_counter_ns()-start+999)//1000
                    snap = world.get_snapshot()
                    assert snap.frame == frame
                    tr = target.get_transform()
                    center = tr.transform(target.bounding_box.location)
                    truth = dict(center=vec(center), velocity=vec(target.get_velocity()),
                                 rotation=[tr.rotation.pitch, tr.rotation.yaw, tr.rotation.roll])
                    source_us = math.floor(snap.timestamp.elapsed_seconds*1000000)
                    record['rows'].append(dict(step=step, frame=frame, source_us=source_us, truth=truth))
                    if step % 2 == 0:
                        start = time.perf_counter_ns()
                        raw = np.frombuffer(d.raw_data, dtype=DTYPE)[::4].copy()
                        transform = np.asarray(d.transform.get_matrix())
                        copy_us = (time.perf_counter_ns()-start+999)//1000
                        assert d.frame == frame
                        name = request['id']+'_s%02d.npz' % step
                        path = args.out/'clouds'/name
                        np.savez_compressed(path, raw=raw, transform=transform, timestamp=d.timestamp)
                        record['sources'].append(dict(step=step, frame=frame, source_us=source_us,
                            acquisition_us=acquisition, copy_us=copy_us, cloud=name, cloud_sha256=sha(path),
                            xyz_count=len(raw), target_returns_audit_only=int((raw['id'] == target.id).sum())))
                outcome['status'] = 'captured'
            except Exception:
                record['exception'] = traceback.format_exc()
                outcome['reason'] = 'capture_exception'
            finally:
                if sensor is not None:
                    sensor.stop()
                    sensor = None
                for actor in reversed(owned):
                    actor.destroy()
                owned = []
                world.tick(20)
            record['outcome'] = dict(outcome)
            logical = (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
            path = args.out/'episodes'/(request['id']+'.json.gz')
            path.write_bytes(gzip.compress(logical, mtime=0))
            outcome.update(file=str(path.relative_to(args.out)), sha256=sha(path),
                           logical_sha256=hashlib.sha256(logical).hexdigest(),
                           rows=len(record['rows']), sources=len(record['sources']))
            outcomes.append(outcome)
            dump(args.out/'outcomes.json', outcomes)
            print(json.dumps(dict(outcome, elapsed_s=time.perf_counter()-begin)), flush=True)
        dump(args.out/'manifest.json', dict(planned=len(plan), captured=sum(v['status']=='captured' for v in outcomes),
             freeze_sha256=sha(E/'freeze.json'), scope='dynamic known-walker development sensing only',
             elapsed_s=time.perf_counter()-begin, goal_complete=False))
    finally:
        if sensor is not None:
            sensor.stop()
        for actor in reversed(owned):
            actor.destroy()
        if world.get_settings().synchronous_mode:
            world.tick(20)
        world.apply_settings(original)
        world.set_weather(weather)
        dump(args.out/'cleanup.json', dict(vehicles=len(world.get_actors().filter('vehicle.*')),
             walkers=len(world.get_actors().filter('walker.*')), sensors=len(world.get_actors().filter('sensor.*')),
             synchronous=world.get_settings().synchronous_mode))


if __name__ == '__main__':
    main()
