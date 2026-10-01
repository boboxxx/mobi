#!/usr/bin/env python3
"""Finite ray capture and conditional certificate evaluation; no driving claim."""
import argparse,csv,hashlib,json,math,queue,socket,time
from pathlib import Path
from dataclasses import replace
import numpy as np
import carla
from geometry import Profile,plane_witnesses,certify
from proof_packet import pack,verify
from run_study import CLASSES,write

DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])

def get_frame(q,frame,timeout=20):
    stale=0
    while True:
        data=q.get(timeout=timeout)
        if data.frame==frame:return data,stale
        if data.frame>frame:raise RuntimeError('Future frame')
        stale+=1

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--host',default='100.109.48.32')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'clouds').mkdir();(a.out/'packets').mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30)
    assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'))
    original=world.get_settings();s=world.get_settings();s.synchronous_mode=True;s.fixed_delta_seconds=.05;s.no_rendering_mode=False;world.apply_settings(s)
    actors=[];sensor=None;rows=[];packets=[];truth=[];started=time.perf_counter()
    try:
        target=None
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                target=ahead[0].transform;break
        if target is None:raise RuntimeError('No corridor')
        query=np.array([target.location.x,target.location.y]);yaw=math.radians(target.rotation.yaw);bp=world.get_blueprint_library()
        for density,(channels,pps) in {'base':(64,500000),'dense':(256,2000000)}.items():
            for layout,(lateral,height) in enumerate([(4.,8.),(8.,6.)]):
                loc=target.location+carla.Location(x=-math.sin(yaw)*lateral,y=math.cos(yaw)*lateral,z=height)
                lidar=bp.find('sensor.lidar.ray_cast_semantic')
                for k,v in dict(channels=str(channels),range='35',points_per_second=str(pps),rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0').items():lidar.set_attribute(k,v)
                sensor=world.spawn_actor(lidar,carla.Transform(loc));q=queue.Queue();sensor.listen(q.put)
                for scenario,offset in [('free',None),('near',0.),('far',8.)]:
                    obstacle=None
                    if offset is not None:
                        loc=target.location+carla.Location(x=math.cos(yaw)*offset,y=math.sin(yaw)*offset,z=.5)
                        obstacle=world.spawn_actor(bp.find('vehicle.audi.a2'),carla.Transform(loc,target.rotation));actors.append(obstacle)
                    warm=0
                    for _ in range(20):
                        f=world.tick(20)
                        try:get_frame(q,f,2);warm+=1
                        except queue.Empty:pass
                        if obstacle:obstacle.apply_control(carla.VehicleControl(brake=1,hand_brake=True))
                    if warm==0:raise RuntimeError('Missing warm-up sensor stream')
                    for step in range(10):
                        begin=time.perf_counter();frame=world.tick(20);data,stale=get_frame(q,frame)
                        raw=np.frombuffer(data.raw_data,dtype=DTYPE)
                        local=np.column_stack([raw['x'],raw['y'],raw['z'],np.ones(len(raw))]);xyz=(local@np.asarray(data.transform.get_matrix()).T)[:,:3]
                        origin=np.array([data.transform.location.x,data.transform.location.y,data.transform.location.z])
                        acquisition_ms=(time.perf_counter()-begin)*1000
                        identifier='%s_%d_%s_%02d'%(density,layout,scenario,step)
                        np.savez_compressed(a.out/'clouds'/(identifier+'.npz'),xyz=xyz,origin=origin,query=query,probe_z=np.array(target.location.z+.6))
                        # Evaluation labels only: never passed to certify/pack.
                        center=None
                        if obstacle:
                            pos=obstacle.get_transform().transform(obstacle.bounding_box.location)
                            center=np.array([pos.x,pos.y])-query
                        truth.append(dict(id=identifier,frame=frame,center_x=float(center[0]) if center is not None else None,
                                          center_y=float(center[1]) if center is not None else None,
                                          bound_x=obstacle.bounding_box.extent.x if obstacle else None,bound_y=obstacle.bounding_box.extent.y if obstacle else None))
                        for thinning in [1,8]:
                            witnesses=plane_witnesses(xyz[::thinning],origin,query,target.location.z+.6)
                            for model,(lo,hi) in CLASSES.items():
                                profile=Profile(r_min=lo,r_max=hi);t=time.perf_counter();primary=certify(witnesses,profile)
                                primary_ms=(time.perf_counter()-t)*1000;chosen=primary;refine_ms=0.
                                if model=='small_core' and primary['validity_s']<.1:
                                    profile=replace(profile,step=.05);t=time.perf_counter();chosen=certify(witnesses,profile)
                                    refine_ms=(time.perf_counter()-t)*1000
                                rows.append(dict(id=identifier,density=density,layout=layout,scenario=scenario,step=step,
                                                 frame=frame,sensor_frame=data.frame,stale_frames=stale,thinning=thinning,model=model,
                                                 primary_ttl_s=primary['validity_s'],chosen_ttl_s=chosen['validity_s'],chosen_step=profile.step,
                                                 witnesses=len(witnesses),clearance_m=chosen['clearance_m'],
                                                 acquisition_ms=acquisition_ms,primary_ms=primary_ms,refine_ms=refine_ms))
                                if step==0:
                                    for horizon in [.1,.2]:
                                        scope=identifier+':'+model;t=time.perf_counter();blob=pack(witnesses,profile,scope,0,horizon)
                                        encoding_ms=(time.perf_counter()-t)*1000;t=time.perf_counter()
                                        ok=bool(blob and verify(blob,profile,scope,.02,.05));verification_ms=(time.perf_counter()-t)*1000
                                        age=(acquisition_ms+primary_ms+refine_ms+encoding_ms+verification_ms)/1000+.02
                                        timed_ok=bool(blob and verify(blob,profile,scope,age,.05))
                                        if blob:(a.out/'packets'/('%s_%d_%s_%s.json'%(identifier,thinning,model,horizon))).write_bytes(blob)
                                        packets.append(dict(id=identifier,density=density,layout=layout,scenario=scenario,thinning=thinning,model=model,
                                                            target_s=horizon,sent=blob is not None,geometry_verified=ok,timing_budget_passed=timed_ok,
                                                            packet_bytes=len(blob) if blob else 0,raw_xyz_bytes=len(xyz[::thinning])*12,
                                                            encoding_ms=encoding_ms,verification_ms=verification_ms,modeled_total_age_s=age))
                    print(json.dumps(dict(completed=density+':'+str(layout)+':'+scenario,world_frames=len(truth))),flush=True)
                    if obstacle:obstacle.destroy();actors.remove(obstacle)
                sensor.stop();sensor.destroy();sensor=None
        write(a.out/'frames.csv',rows);write(a.out/'packet_results.csv',packets);write(a.out/'evaluation_labels.csv',truth)
        manifest=dict(host=socket.gethostname(),client=client.get_client_version(),server=client.get_server_version(),map=world.get_map().name,
                      world_frames=len(truth),analysis_rows=len(rows),elapsed_s=time.perf_counter()-started,
                      source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py') if not f.name.startswith('._')},
                      scope='New CARLA stationary rays; opaque-core contract is not formally established for arbitrary CARLA meshes; labels evaluation-only; no driving controller.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    finally:
        if sensor:sensor.stop();sensor.destroy()
        for actor in actors:
            if actor.is_alive:actor.destroy()
        world.apply_settings(original)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous_mode=world.get_settings().synchronous_mode),indent=2)+'\n')

if __name__=='__main__':main()
