#!/usr/bin/env python3
"""Finite real-sensor prerequisite audit, not a closed-loop driving benchmark.

Ground returns cover sampled cells only. A passing gate is necessary for this
representation, not proof of continuous empty volume or real-world safety.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import queue
import socket
import time
import numpy as np
import carla
from certificate import lifetime

DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])


def frame_data(q, frame, timeout=20):
    stale=0
    while True:
        data=q.get(timeout=timeout)
        if data.frame==frame:return data,stale
        if data.frame>frame:raise RuntimeError('Sensor frame ahead of requested world frame')
        stale+=1


def classify(xyz, target, cell):
    yaw=math.radians(target.rotation.yaw); dx=xyz[:,0]-target.location.x;dy=xyz[:,1]-target.location.y
    along=dx*math.cos(yaw)+dy*math.sin(yaw);across=-dx*math.sin(yaw)+dy*math.cos(yaw)
    height=xyz[:,2]-target.location.z
    inside=(along>=-5)&(along<5)&(across>=-1.5)&(across<1.5)
    ground=inside&(height>=-.3)&(height<.25)
    obstacle=inside&(height>=.3)&(height<=3)
    cells={(int((a+5)/cell),int((b+1.5)/cell)) for a,b in zip(along[ground],across[ground])}
    required=int(round(10/cell))*int(round(3/cell))
    fraction=len(cells)/required
    state='occupied' if np.any(obstacle) else ('free' if len(cells)==required else 'unknown')
    return state,fraction,int(np.sum(obstacle)),len(cells),required


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',default='100.109.48.32');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--frames',type=int,default=20);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    client=carla.Client(a.host,2000);client.set_timeout(30)
    if client.get_client_version()!=client.get_server_version():raise RuntimeError('Client/server mismatch')
    world=client.get_world();road_map=world.get_map()
    if len(world.get_actors().filter('vehicle.*')):raise RuntimeError('Existing vehicle actors: refusing to modify active scene')
    original=world.get_settings();settings=world.get_settings();settings.synchronous_mode=True
    settings.fixed_delta_seconds=.05;settings.no_rendering_mode=False;world.apply_settings(settings)
    rows=[];actors=[];sensor=None;setup=[];start=time.perf_counter()
    try:
        target=None
        for spawn in road_map.get_spawn_points():
            wp=road_map.get_waypoint(spawn.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:
                target=ahead[0].transform;break
        if target is None:raise RuntimeError('No suitable straight corridor')
        bp=world.get_blueprint_library()
        for layout,(lateral,height) in enumerate(((4.,8.),(8.,6.))):
            yaw=math.radians(target.rotation.yaw)
            position=target.location+carla.Location(x=-math.sin(yaw)*lateral,y=math.cos(yaw)*lateral,z=height)
            lidar=bp.find('sensor.lidar.ray_cast_semantic')
            for key,value in {'channels':'64','range':'35','points_per_second':'500000','rotation_frequency':'20',
                              'upper_fov':'10','lower_fov':'-90','sensor_tick':'0'}.items():lidar.set_attribute(key,value)
            sensor=world.spawn_actor(lidar,carla.Transform(position));q=queue.Queue();sensor.listen(q.put)
            for scenario in ('free','occupied'):
                obstacle=None
                if scenario=='occupied':
                    tr=carla.Transform(target.location+carla.Location(z=.5),target.rotation)
                    obstacle=world.spawn_actor(bp.find('vehicle.audi.a2'),tr);actors.append(obstacle)
                warmup_received=0
                for _ in range(20):
                    f=world.tick(20)
                    # The first tick may precede completion of stream subscription.
                    # Only warm-up may skip a missing frame; measured frames may not.
                    try:
                        frame_data(q,f,timeout=2);warmup_received+=1
                    except queue.Empty:
                        pass
                    if obstacle:obstacle.apply_control(carla.VehicleControl(brake=1,hand_brake=True))
                if warmup_received==0:raise RuntimeError('No sensor frames in bounded warm-up')
                setup.append(dict(layout=layout,scenario=scenario,sensor=str(sensor.get_transform()),target=str(target),
                                  warmup_frames_received=warmup_received,
                                  actual_obstacle_transform=str(obstacle.get_transform()) if obstacle else None))
                for step in range(a.frames):
                    begin=time.perf_counter();f=world.tick(20);data,stale=frame_data(q,f)
                    points=np.frombuffer(data.raw_data,dtype=DTYPE)
                    local=np.column_stack([points['x'],points['y'],points['z'],np.ones(len(points))])
                    xyz=(local@np.asarray(data.transform.get_matrix()).T)[:,:3]
                    for thinning in (1,8):
                        for cell in (.5,1.):
                            state,cov,count,covered,total=classify(xyz[::thinning],target,cell)
                            # Derived length is supplied corridor geometry, not an estimated open-road bound.
                            ttl=lifetime(5,.25,13.9,3,.02,covered=cov==1,observed_free=state=='free')
                            rows.append(dict(layout=layout,scenario=scenario,step=step,frame=f,sensor_frame=data.frame,
                                             thinning=thinning,cell_m=cell,state=state,coverage=cov,covered_cells=covered,
                                             required_cells=total,obstacle_points=count,raw_points=len(points),validity_s=ttl,
                                             stale_frames=stale,loop_ms=(time.perf_counter()-begin)*1000))
                    if step==0:
                        np.savez_compressed(a.out/('points_%d_%s.npz'%(layout,scenario)),xyz=xyz)
                if obstacle:obstacle.destroy();actors.remove(obstacle)
            sensor.stop();sensor.destroy();sensor=None
        summary=[]
        for layout in range(2):
            for scenario in ('free','occupied'):
                for thinning in (1,8):
                    for cell in (.5,1.):
                        part=[r for r in rows if (r['layout'],r['scenario'],r['thinning'],r['cell_m'])==(layout,scenario,thinning,cell)]
                        summary.append(dict(layout=layout,scenario=scenario,thinning=thinning,cell_m=cell,frames=len(part),
                                            mean_coverage=float(np.mean([r['coverage'] for r in part])),
                                            free_fraction=float(np.mean([r['state']=='free' for r in part])),
                                            occupied_fraction=float(np.mean([r['state']=='occupied' for r in part])),
                                            unknown_fraction=float(np.mean([r['state']=='unknown' for r in part]))))
        for name,data in [('frames.csv',rows),('summary.csv',summary)]:
            with (a.out/name).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
        # Primary representation fixed at 0.5m, no artificial thinning.
        primary=[r for r in summary if r['thinning']==1 and r['cell_m']==.5]
        passed=all(r['free_fraction']==1 if r['scenario']=='free' else r['occupied_fraction']==1 for r in primary)
        manifest=dict(host=socket.gethostname(),client=client.get_client_version(),server=client.get_server_version(),
                      map=road_map.name,world_frames=4*a.frames,record_rows=len(rows),elapsed_s=time.perf_counter()-start,
                      primary_gate_passed=passed,setup=setup,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      scope='Actual CARLA semantic ground-truth LiDAR, stationary corridor coverage gate. No driving or detector robustness claim.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest),flush=True)
    finally:
        if sensor is not None:
            sensor.stop();sensor.destroy()
        for actor in actors:
            if actor.is_alive:actor.destroy()
        world.apply_settings(original)


if __name__=='__main__':main()
