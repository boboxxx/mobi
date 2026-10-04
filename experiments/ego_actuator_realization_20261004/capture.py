#!/usr/bin/env python3
"""Finite actual ego physics; no velocity override and no inferred safety grant."""
import argparse
import gzip
import hashlib
import json
import math
import socket
import time
import traceback
from pathlib import Path
import carla

E = Path(__file__).resolve().parent
ROOT = E.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def control(c):
    return {k:getattr(c, k) for k in ('throttle', 'brake', 'steer', 'hand_brake', 'reverse', 'manual_gear_shift', 'gear')}


def sample(world, vehicle, frame):
    snap = world.get_snapshot()
    assert snap.frame == frame
    actor = snap.find(vehicle.id)
    assert actor is not None
    tr = actor.get_transform()
    center = tr.transform(carla.Location(*vec(vehicle.bounding_box.location)))
    return dict(frame=frame, timestamp=float(snap.timestamp.elapsed_seconds), location=vec(tr.location), rotation=[tr.rotation.pitch, tr.rotation.yaw, tr.rotation.roll], matrix=tr.get_matrix(), center=vec(center), velocity=vec(actor.get_velocity()), body_vertices=[vec(v) for v in vehicle.bounding_box.get_world_vertices(tr)], actual=control(vehicle.get_control()))


def dump(p, d):
    p.write_text(json.dumps(d, indent=2, sort_keys=True, allow_nan=False)+'\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    f = json.loads((E/'freeze.json').read_bytes())
    for section in ('sources', 'inputs'):
        for n, h in f[section].items():
            assert sha(ROOT/n) == h, n
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out/'episodes').mkdir()
    plan = json.loads((E/'plan.json').read_bytes())
    dump(a.out/'plan.json', plan)
    client = carla.Client('100.109.48.32', 2000)
    client.set_timeout(30)
    assert client.get_client_version() == client.get_server_version() == '0.9.15'
    world = client.get_world()
    assert world.get_map().name.endswith('Town10HD_Opt')
    assert not any(x.type_id.startswith(('vehicle.', 'sensor.', 'walker.')) for x in world.get_actors())
    original, weather = world.get_settings(), world.get_weather()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = .05
    settings.substepping = True
    settings.max_substep_delta_time = .01
    settings.max_substeps = 10
    world.apply_settings(settings)
    world.set_weather(carla.WeatherParameters.ClearNoon)
    vehicle = sensor = None
    outcomes = []
    start = time.perf_counter()
    try:
        spawns = []
        for tr in world.get_map().get_spawn_points():
            wp = world.get_map().get_waypoint(tr.location)
            ahead = wp.next(35)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180) < 3:
                spawns.append(tr)
                if len(spawns) == 3:
                    break
        assert len(spawns) == 3
        dump(a.out/'spawns.json', [dict(location=vec(t.location), rotation=[t.rotation.pitch,t.rotation.yaw,t.rotation.roll]) for t in spawns])
        for request in plan:
            rows, events = [], []
            outcome = dict(request=request, status='failed')
            record = dict(request=request, rows=rows, collisions=events)
            try:
                tr = spawns[request['location']]
                vehicle = world.try_spawn_actor(world.get_blueprint_library().find('vehicle.audi.a2'), tr)
                if vehicle is None:
                    outcome['reason'] = 'spawn_failed'
                else:
                    sensor = world.spawn_actor(world.get_blueprint_library().find('sensor.other.collision'), carla.Transform(), attach_to=vehicle)
                    def collision(e):
                        events.append(dict(frame=e.frame, other=e.other_actor.type_id, impulse=vec(e.normal_impulse)))
                    sensor.listen(collision)
                    pc = vehicle.get_physics_control()
                    record['physics'] = dict(mass=pc.mass, max_rpm=pc.max_rpm, use_gear_autobox=pc.use_gear_autobox, gear_switch_time=pc.gear_switch_time, clutch_strength=pc.clutch_strength, torque_curve=[[v.x,v.y] for v in pc.torque_curve], forward_gears=[dict(ratio=g.ratio,down_ratio=g.down_ratio,up_ratio=g.up_ratio) for g in pc.forward_gears])
                    bb = vehicle.bounding_box
                    record['body'] = dict(extent=vec(bb.extent), offset=vec(bb.location), rotation=[bb.rotation.pitch,bb.rotation.yaw,bb.rotation.roll])
                    manual = request['mode'] != 'automatic45'
                    emergency = False
                    def tick(phase, throttle, brake):
                        c = carla.VehicleControl(throttle=throttle, brake=brake, steer=0., hand_brake=False, reverse=False, manual_gear_shift=manual, gear=1 if manual else 0)
                        wall0 = time.perf_counter_ns()
                        response = client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,c)], False)
                        wall1 = time.perf_counter_ns()
                        assert not any(x.error for x in response)
                        frame = world.tick(20)
                        wall2 = time.perf_counter_ns()
                        row = sample(world, vehicle, frame)
                        row.update(phase=phase, requested=control(c), command_wall_ns=wall1-wall0, tick_wall_ns=wall2-wall1)
                        rows.append(row)
                        return row
                    for _ in range(40):
                        tick('settle', 0., 1.)
                    record['initial'] = rows[-1]
                    if math.hypot(*rows[-1]['velocity'][:2]) >= .02:
                        outcome['reason'] = 'settling_failed'
                    else:
                        for _ in range(60):
                            speed = math.hypot(*rows[-1]['velocity'][:2])
                            if request['stage'] == 'feedback' and speed > 1.5:
                                emergency = True
                            if emergency:
                                throttle, brake = 0., 1.
                            elif request['stage'] == 'feedback':
                                target = request['target_mps']
                                throttle = .8 if speed < target else 0.
                                brake = min(.4,max(0.,.4*(speed-target))) if speed > target+.05 else 0.
                            else:
                                throttle, brake = (.8 if request['mode']=='manual80' else .45), 0.
                            tick('go', throttle, brake)
                        record['go_end'] = rows[-1]
                        for _ in range(80):
                            tick('brake', 0., 1.)
                        outcome['status'] = 'captured' if not emergency else 'refused'
                        if emergency:
                            outcome['reason'] = 'speed_limit_exceeded'
                    time.sleep(.03)
                    record['collisions'] = list(events)
            except Exception:
                outcome['reason'] = 'capture_exception'
                record['exception'] = traceback.format_exc()
            finally:
                if sensor is not None:
                    sensor.stop()
                    assert sensor.destroy()
                    sensor = None
                if vehicle is not None:
                    assert vehicle.destroy()
                    vehicle = None
                world.tick(20)
            record['collisions'] = list(events)
            record['outcome'] = outcome
            logical = (json.dumps(record,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n').encode()
            file = a.out/'episodes'/(request['id']+'.json.gz')
            file.write_bytes(gzip.compress(logical,mtime=0))
            outcome.update(file=str(file.relative_to(a.out)),archive_bytes=file.stat().st_size,archive_sha256=sha(file),logical_bytes=len(logical),logical_sha256=hashlib.sha256(logical).hexdigest(),rows=len(rows))
            outcomes.append(outcome)
            dump(a.out/'outcomes.json',outcomes)
            print(json.dumps(dict(id=request['id'],status=outcome['status'],rows=len(rows),elapsed_s=time.perf_counter()-start)),flush=True)
        assert len(outcomes)==36
        dump(a.out/'manifest.json',dict(host=socket.gethostname(),client='0.9.15',server=client.get_server_version(),map=world.get_map().name,plan_sha256=sha(E/'plan.json'),freeze_sha256=sha(E/'freeze.json'),planned=36,captured=sum(v['status']=='captured' for v in outcomes),elapsed_s=time.perf_counter()-start,scope='Finite physical actuation realization only; no evidence, conditional policy certificate, continuous bound, radio or collision-risk guarantee.',goal_complete=False))
    finally:
        if sensor is not None:
            sensor.stop();sensor.destroy()
        if vehicle is not None:
            vehicle.destroy()
        if world.get_settings().synchronous_mode:
            world.tick(20)
        world.apply_settings(original)
        world.set_weather(weather)
        dump(a.out/'cleanup.json',dict(vehicles=len(world.get_actors().filter('vehicle.*')),walkers=len(world.get_actors().filter('walker.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode))


if __name__ == '__main__':
    main()
