#!/usr/bin/env python3
import argparse,hashlib,json,math,queue,socket,time
from pathlib import Path
import numpy as np
import carla
from proof import Contract,Scope,pack,verify,TIME_SCALE
from optimized_local import renew
from run_replay import profiles
from run_study import write

DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])


def matched(q,frame,timeout=20):
    stale=0
    while True:
        data=q.get(timeout=timeout)
        if data.frame==frame:return data,stale
        if data.frame>frame:raise RuntimeError('Future sensor frame')
        stale+=1


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    for sub in ['clouds','packets']:(a.out/sub).mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30)
    assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'))
    original=world.get_settings();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;world.apply_settings(settings)
    actors=[];sensor=None;rows=[];p=profiles();contract=Contract();start=time.perf_counter()
    try:
        target=None
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                target=ahead[0].transform;break
        if target is None:raise RuntimeError('No corridor')
        query=np.array([target.location.x,target.location.y]);yaw=math.radians(target.rotation.yaw);forward=np.array([math.cos(yaw),math.sin(yaw)])
        bp=world.get_blueprint_library()
        for layout,(lateral,height) in enumerate([(4.,8.),(8.,6.)]):
            lidar=bp.find('sensor.lidar.ray_cast_semantic')
            for k,v in dict(channels='256',range='35',points_per_second='2000000',rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0').items():lidar.set_attribute(k,v)
            loc=target.location+carla.Location(x=-forward[1]*lateral,y=forward[0]*lateral,z=height)
            sensor=world.spawn_actor(lidar,carla.Transform(loc));q=queue.Queue();sensor.listen(q.put)
            loc=target.location+carla.Location(x=forward[0]*8,y=forward[1]*8,z=.5)
            vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),carla.Transform(loc,carla.Rotation(yaw=target.rotation.yaw+180)));actors.append(vehicle)
            warm=0
            for _ in range(20):
                frame=world.tick(20)
                try:matched(q,frame,2);warm+=1
                except queue.Empty:pass
                vehicle.apply_control(carla.VehicleControl(brake=1,hand_brake=True))
            if not warm:raise RuntimeError('No sensor stream')
            vehicle.apply_control(carla.VehicleControl(brake=0,hand_brake=False))
            scope=Scope('dynamic-v2:view'+str(layout),world.get_map().name,tuple(query),target.location.z+.6)
            template=None
            for step in range(64):
                vehicle.set_target_velocity(carla.Vector3D(x=-4*forward[0],y=-4*forward[1],z=0))
                begin=time.perf_counter();frame=world.tick(20);data,stale=matched(q,frame)
                raw=np.frombuffer(data.raw_data,dtype=DTYPE);local=np.column_stack([raw['x'],raw['y'],raw['z'],np.ones(len(raw))])
                xyz=(local@np.asarray(data.transform.get_matrix()).T)[:,:3]
                origin=np.array([data.transform.location.x,data.transform.location.y,data.transform.location.z])
                acquisition_ms=(time.perf_counter()-begin)*1000;stamp=float(data.timestamp)
                begin=time.perf_counter()
                if step==0:
                    blob=pack(xyz,origin,stamp,stamp,p,scope,contract,sequence=step)
                    template=blob
                else:blob=renew(template,xyz,origin,stamp,stamp,p,scope,contract,step) if template else None
                source_ms=(time.perf_counter()-begin)*1000
                begin=time.perf_counter();ok=bool(blob and verify(blob,p,scope,contract,stamp+.02,.05))
                receiver_ms=(time.perf_counter()-begin)*1000
                age=acquisition_ms/1000+(source_ms+receiver_ms)/1000+.02
                timed=bool(blob and verify(blob,p,scope,contract,stamp+age,.05))
                identifier='view%d_%03d'%(layout,step)
                if blob:(a.out/'packets'/(identifier+'.json')).write_bytes(blob)
                np.savez_compressed(a.out/'clouds'/(identifier+'.npz'),xyz=xyz,origin=origin,query=query,probe_z=np.array(scope.plane_z),timestamp=np.array(stamp))
                # These labels are NEVER passed to the encoder or receiver.
                position=vehicle.get_transform().transform(vehicle.bounding_box.location);velocity=vehicle.get_velocity()
                center=np.array([position.x,position.y])-query
                rows.append(dict(id=identifier,layout=layout,step=step,frame=frame,sensor_frame=data.frame,stale_frames=stale,timestamp=stamp,
                                 center_x=center[0],center_y=center[1],vx=velocity.x,vy=velocity.y,vz=velocity.z,
                                 bound_x=vehicle.bounding_box.extent.x,bound_y=vehicle.bounding_box.extent.y,
                                 template_available=template is not None,geometry_verified=ok,timing_budget_passed=timed,
                                 packet_bytes=len(blob) if blob else 0,acquisition_ms=acquisition_ms,source_ms=source_ms,receiver_ms=receiver_ms,
                                 total_modeled_age_s=age))
                if step%16==15:print(json.dumps(dict(layout=layout,step=step,frames=len(rows))),flush=True)
            vehicle.destroy();actors.remove(vehicle);sensor.stop();sensor.destroy();sensor=None
            world.tick(20)
        write(a.out/'frames.csv',rows)
        manifest=dict(host=socket.gethostname(),world_frames=len(rows),map=world.get_map().name,
                      geometry=sum(r['geometry_verified'] for r in rows),timing=sum(r['timing_budget_passed'] for r in rows),elapsed_s=time.perf_counter()-start,
                      source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['capture_dynamic_local.py','proof.py','optimized_local.py','optimized.py','run_replay.py']},
                      protocol_sha256=hashlib.sha256(Path(__file__).with_name('DYNAMIC_LOCAL_FOLLOWUP.md').read_bytes()).hexdigest(),
                      scope='New dynamic CARLA scans; receiver decision monitor, no ego controller. Simultaneous rays within each frame, modeled communication/action budget.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        if sensor:sensor.stop();sensor.destroy()
        for actor in actors:
            if actor.is_alive:actor.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
