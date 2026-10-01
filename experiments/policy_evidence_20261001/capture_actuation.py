#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import carla


def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def sample(vehicle):
    tr=vehicle.get_transform();v=vehicle.get_velocity()
    return dict(x=tr.location.x,y=tr.location.y,z=tr.location.z,yaw=tr.rotation.yaw,vx=v.x,vy=v.y,vz=v.z,speed=math.hypot(v.x,v.y))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'episodes').mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'))
    original=world.get_settings();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings)
    vehicle=sensor=None;summaries=[];bp=world.get_blueprint_library();start=time.perf_counter()
    try:
        spawn=None
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(35)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                spawn=tr;break
        if spawn is None:raise RuntimeError('No straight corridor')
        for repeat in range(2):
          for target in [.5,1.,2.]:
            for brake in [.3,.5,.8]:
                vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),spawn)
                events=[];sensor=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=vehicle)
                sensor.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
                vehicle.apply_control(carla.VehicleControl(brake=1.,steer=0.))
                for _ in range(20):world.tick(20)
                initial=sample(vehicle);rows=[];reached=False
                for phase,ticks,throttle,command_brake in [('drive',120,.2,0.),('brake',40,0.,brake)]:
                    for step in range(ticks):
                        before=sample(vehicle);vehicle.apply_control(carla.VehicleControl(throttle=throttle,brake=command_brake,steer=0.));frame=world.tick(20);now=sample(vehicle);stamp=world.get_snapshot().timestamp.elapsed_seconds
                        rows.append(dict(phase=phase,step=step,frame=frame,timestamp=stamp,throttle=throttle,brake=command_brake,steer=0.,before_speed=before['speed'],sampled_acceleration=(now['speed']-before['speed'])/.05,**now))
                        if phase=='drive' and now['speed']>=target:reached=True;break
                identifier='r%d_v%s_b%s'%(repeat,target,brake);write(a.out/'episodes'/(identifier+'.csv'),rows)
                summaries.append(dict(id=identifier,repeat=repeat,target=target,brake=brake,target_reached=reached,initial=json.dumps(initial),box_x=vehicle.bounding_box.extent.x,box_y=vehicle.bounding_box.extent.y,box_z=vehicle.bounding_box.extent.z,rows=len(rows),collisions=len(events),events=json.dumps(events)))
                sensor.stop();sensor.destroy();sensor=None;vehicle.destroy();vehicle=None;world.tick(20)
                write(a.out/'summary.partial.csv',summaries);print(json.dumps(dict(id=identifier,target_reached=reached,rows=len(rows),collisions=len(events))),flush=True)
        (a.out/'summary.partial.csv').replace(a.out/'summary.csv')
        manifest=dict(host=socket.gethostname(),episodes=len(summaries),elapsed_s=time.perf_counter()-start,map=world.get_map().name,carla_version=client.get_client_version(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(Path(__file__).with_name('CALIBRATION_PROTOCOL.md').read_bytes()).hexdigest(),scope='Own-vehicle open-loop actuator audit, no perception-evidence admission and no real-world calibration.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        if sensor:sensor.stop();sensor.destroy()
        if vehicle and vehicle.is_alive:vehicle.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
