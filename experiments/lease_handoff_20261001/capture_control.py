#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import carla


def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def sample(world,vehicle,frame=None):
    snapshot=world.get_snapshot()
    if frame is not None:assert snapshot.frame==frame
    actor=snapshot.find(vehicle.id);assert actor is not None
    tr=actor.get_transform();v=actor.get_velocity()
    return dict(frame=snapshot.frame,timestamp=snapshot.timestamp.elapsed_seconds,x=tr.location.x,y=tr.location.y,z=tr.location.z,yaw=tr.rotation.yaw,vx=v.x,vy=v.y,vz=v.z,speed=math.hypot(v.x,v.y))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'episodes').mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'));original=world.get_settings();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings)
    vehicle=sensor=None;summaries=[];bp=world.get_blueprint_library();start=time.perf_counter()
    try:
        spawns=[]
        for transform in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(transform.location);ahead=wp.next(35)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                spawns.append(transform)
                if len(spawns)==3:break
        assert len(spawns)==3
        for location,spawn in enumerate(spawns):
          for target in [.5,1.]:
           for mode in ['ackermann','relay']:
            vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),spawn);events=[];sensor=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=vehicle);sensor.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
            def raw(throttle,brake):
                response=client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,carla.VehicleControl(throttle=throttle,brake=brake,steer=0.))],False)
                assert not any(r.error for r in response)
            for _ in range(20):raw(0.,1.);world.tick(20)
            initial=sample(world,vehicle);rows=[];ack=vehicle.get_ackermann_controller_settings();ack_values={k:getattr(ack,k) for k in ['speed_kp','speed_ki','speed_kd','accel_kp','accel_ki','accel_kd']}
            for phase,ticks in [('drive',160),('backup',40)]:
                for step in range(ticks):
                    before=sample(world,vehicle);throttle=brake=None
                    if phase=='backup':throttle=0.;brake=1.;raw(throttle,brake)
                    elif mode=='ackermann':
                        response=client.apply_batch_sync([carla.command.ApplyVehicleAckermannControl(vehicle.id,carla.VehicleAckermannControl(steer=0.,speed=target,acceleration=.5))],False)
                        assert not any(r.error for r in response)
                    else:
                        throttle=.45 if before['speed']<target else 0.;brake=min(.2,.2*(before['speed']-target)) if before['speed']>target+.1 else 0.;raw(throttle,brake)
                    frame=world.tick(20);state=sample(world,vehicle,frame);c=vehicle.get_control();controls={'actual_'+k:getattr(c,k) for k in ['throttle','brake','steer','gear','hand_brake','reverse']}
                    rows.append(dict(phase=phase,step=step,throttle=throttle,brake=brake,desired_speed=target,desired_acceleration=.5 if mode=='ackermann' and phase=='drive' else None,before_speed=before['speed'],sampled_acceleration=(state['speed']-before['speed'])/.05,**controls,**state))
            identifier='loc%s_v%s_%s'%(location,target,mode);write(a.out/'episodes'/(identifier+'.csv'),rows);box=vehicle.bounding_box
            summaries.append(dict(id=identifier,location=location,target=target,mode=mode,initial=json.dumps(initial),ackermann_settings=json.dumps(ack_values),box_x=box.extent.x,box_y=box.extent.y,box_offset_x=box.location.x,box_offset_y=box.location.y,rows=len(rows),collisions=len(events),events=json.dumps(events)))
            sensor.stop();sensor.destroy();sensor=None;vehicle.destroy();vehicle=None;world.tick(20);write(a.out/'summary.partial.csv',summaries);print(json.dumps(dict(id=identifier,final_speed=rows[-1]['speed'],collisions=len(events))),flush=True)
        (a.out/'summary.partial.csv').replace(a.out/'summary.csv');src=Path(__file__)
        manifest=dict(host=socket.gethostname(),episodes=len(summaries),elapsed_s=time.perf_counter()-start,map=world.get_map().name,carla=client.get_client_version(),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(src.with_name('CONTROL_PROTOCOL.md').read_bytes()).hexdigest(),scope='Actual continuous-control and backup diagnostics; no evidence-guided driving or calibrated physical bound.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        if sensor:sensor.stop();sensor.destroy()
        if vehicle and vehicle.is_alive:vehicle.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
