#!/usr/bin/env python3
import argparse,csv,gzip,hashlib,json,math,socket,time
from pathlib import Path
import numpy as np
import carla


def sample(world,vehicle,frame=None):
    s=world.get_snapshot()
    if frame is not None:assert s.frame==frame
    actor=s.find(vehicle.id);assert actor is not None
    tr=actor.get_transform();v=actor.get_velocity();c=vehicle.get_control()
    return dict(frame=s.frame,timestamp=s.timestamp.elapsed_seconds,x=tr.location.x,y=tr.location.y,z=tr.location.z,yaw=tr.rotation.yaw,pitch=tr.rotation.pitch,roll=tr.rotation.roll,body_vertices=[[v.x,v.y,v.z] for v in vehicle.bounding_box.get_world_vertices(tr)],vx=v.x,vy=v.y,vz=v.z,speed=math.hypot(v.x,v.y),actual_throttle=c.throttle,actual_brake=c.brake,actual_steer=c.steer,actual_gear=c.gear)


def relay(speed,target):return (.45 if speed<target else 0.,min(.2,.2*(speed-target)) if speed>target+.1 else 0.)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'episodes').mkdir()
    plan=[]
    for role,n,seed in [('train',100,2026100101),('calibration',299,2026100102),('test',400,2026100103)]:
        rng=np.random.Generator(np.random.PCG64(seed))
        for i in range(n):plan.append(dict(id='%s_%04d'%(role,i),role=role,location=int(rng.integers(3)),target=float(rng.uniform(.3,1.2)),prefix_ticks=int(rng.integers(20,160))))
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15';world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'));original=world.get_settings();old_weather=world.get_weather();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings);world.set_weather(carla.WeatherParameters.ClearNoon)
    vehicle=sensor=None;bp=world.get_blueprint_library();summaries=[];start=time.perf_counter()
    try:
        spawns=[]
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(35)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                spawns.append(tr)
                if len(spawns)==3:break
        assert len(spawns)==3
        for ordinal,request in enumerate(plan):
            vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),spawns[request['location']]);events=[];sensor=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=vehicle);sensor.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
            world.tick(20);initial=sample(world,vehicle);rows=[]
            def step(phase,throttle,brake):
                before=sample(world,vehicle);rs=client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,carla.VehicleControl(throttle=throttle,brake=brake,steer=0.))],False);assert not any(r.error for r in rs)
                state=sample(world,vehicle,world.tick(20));rows.append(dict(phase=phase,command_throttle=throttle,command_brake=brake,before_speed=before['speed'],acceleration=(state['speed']-before['speed'])/.05,**state));return state
            for _ in range(20):step('warm',0.,1.)
            for _ in range(request['prefix_ticks']):step('prefix',*relay(sample(world,vehicle)['speed'],request['target']))
            reference=sample(world,vehicle);throttle,brake=relay(reference['speed'],request['target']);features=dict(speed=reference['speed'],last_acceleration=rows[-1]['acceleration'],gear_is_1=int(reference['actual_gear']==1),planned_throttle=throttle,planned_brake=brake,target=request['target'])
            step('command',throttle,brake)
            for _ in range(40):step('backup',0.,1.)
            time.sleep(.01);box=vehicle.bounding_box;physics=vehicle.get_physics_control();record=dict(request=request,initial=initial,reference=reference,features=features,body=dict(half_length=box.extent.x,half_width=box.extent.y,offset_x=box.location.x,offset_y=box.location.y,half_height=box.extent.z,offset_z=box.location.z,rotation=dict(pitch=box.rotation.pitch,yaw=box.rotation.yaw,roll=box.rotation.roll)),physics=dict(mass=physics.mass,max_rpm=physics.max_rpm,drag_coefficient=physics.drag_coefficient),collisions=list(events),rows=rows)
            dest=a.out/'episodes'/(request['id']+'.json.gz');dest.write_bytes(gzip.compress(json.dumps(record,separators=(',',':'),allow_nan=False).encode(),mtime=0));summaries.append(dict(**request,reference_speed=reference['speed'],rows=len(rows),collisions=len(events),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            sensor.stop();sensor.destroy();sensor=None;vehicle.destroy();vehicle=None;world.tick(20)
            with (a.out/'summary.partial.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
            if ordinal%25==0:print(json.dumps(dict(complete=ordinal+1,total=len(plan),elapsed_s=time.perf_counter()-start)),flush=True)
        (a.out/'summary.partial.csv').replace(a.out/'summary.csv');src=Path(__file__);manifest=dict(host=socket.gethostname(),carla=client.get_client_version(),numpy=np.__version__,map=world.get_map().name,episodes=len(plan),elapsed_s=time.perf_counter()-start,source_file=src.name,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),pose_addendum_sha256=hashlib.sha256(src.with_name('POSE_ADDENDUM.md').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(src.with_name('PROTOCOL.md').read_bytes()).hexdigest(),plan_sha256=hashlib.sha256((a.out/'plan.json').read_bytes()).hexdigest(),scope='Randomized independent-episode sampled actuator diagnostics; no calibrated physical hard bound or evidence-guided driving.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        if sensor:sensor.stop();sensor.destroy()
        if vehicle and vehicle.is_alive:vehicle.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original);world.set_weather(old_weather);(a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
