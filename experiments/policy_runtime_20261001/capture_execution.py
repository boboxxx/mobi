#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import carla


def write(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def sample(world,vehicle,frame=None):
    snapshot=world.get_snapshot()
    if frame is not None:assert snapshot.frame==frame
    actor=snapshot.find(vehicle.id);assert actor is not None
    tr=actor.get_transform();v=actor.get_velocity()
    return dict(frame=snapshot.frame,timestamp=snapshot.timestamp.elapsed_seconds,x=tr.location.x,y=tr.location.y,z=tr.location.z,yaw=tr.rotation.yaw,vx=v.x,vy=v.y,vz=v.z,speed=math.hypot(v.x,v.y))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'episodes').mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'));original=world.get_settings()
    settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings)
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
          for target in [0.,.5,1.]:
           for hold in [.05,.10]:
            for go in [True,False]:
                vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),spawn);events=[]
                sensor=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=vehicle);sensor.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
                def tick(throttle,brake):
                    responses=client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,carla.VehicleControl(throttle=throttle,brake=brake,steer=0.))],False)
                    assert not any(r.error for r in responses)
                    frame=world.tick(20);state=sample(world,vehicle,frame);control=vehicle.get_control()
                    state.update({'actual_'+k:getattr(control,k) for k in ['throttle','brake','steer','gear','hand_brake','reverse']})
                    return state
                for _ in range(20):tick(0.,1.)
                initial=sample(world,vehicle);rows=[];reached=target==0
                if target>0:
                    for step in range(180):
                        state=tick(.5,0.);rows.append(dict(phase='prepare',step=step,throttle=.5,brake=0.,**state))
                        if state['speed']>=target:reached=True;break
                reference=sample(world,vehicle)
                for phase,ticks,throttle,brake in [('hold',round(hold/.05),0.,1.),('go',1,.5 if go else 0.,0. if go else 1.),('backup',40,0.,1.)]:
                    for step in range(ticks):rows.append(dict(phase=phase,step=step,throttle=throttle,brake=brake,**tick(throttle,brake)))
                identifier='loc%s_v%s_hold%s_%s'%(location,target,hold,'go' if go else 'stop');write(a.out/'episodes'/(identifier+'.csv'),rows)
                box=vehicle.bounding_box
                summaries.append(dict(id=identifier,go=go,location=location,target=target,hold=hold,target_reached=reached,initial=json.dumps(initial),reference=json.dumps(reference),box_x=box.extent.x,box_y=box.extent.y,box_z=box.extent.z,box_offset_x=box.location.x,box_offset_y=box.location.y,box_yaw=box.rotation.yaw,rows=len(rows),collisions=len(events),events=json.dumps(events)))
                sensor.stop();sensor.destroy();sensor=None;vehicle.destroy();vehicle=None;world.tick(20)
                write(a.out/'summary.partial.csv',summaries);print(json.dumps(dict(id=identifier,reached=reached,reference_speed=reference['speed'],collisions=len(events))),flush=True)
        (a.out/'summary.partial.csv').replace(a.out/'summary.csv')
        src=Path(__file__);manifest=dict(host=socket.gethostname(),episodes=len(summaries),elapsed_s=time.perf_counter()-start,map=world.get_map().name,carla=client.get_client_version(),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(src.with_name('EXECUTION_PROTOCOL.md').read_bytes()).hexdigest(),scope='Own-vehicle realization diagnostic of specified hold/go/brake policy; no evidence-guided action or statistical calibration.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        if sensor:sensor.stop();sensor.destroy()
        if vehicle and vehicle.is_alive:vehicle.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
