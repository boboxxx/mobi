#!/usr/bin/env python3
"""Fresh disjoint calibration/test episodes. Labels remain evaluation-only."""
import argparse,hashlib,json,math,queue,socket,time
from pathlib import Path
import numpy as np
import carla
DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])
BLUEPRINTS=['vehicle.audi.a2','vehicle.tesla.model3','vehicle.mercedes.sprinter','vehicle.diamondback.century','vehicle.kawasaki.ninja','walker.pedestrian.0001']
def vec(v):return [float(v.x),float(v.y),float(v.z)]
def tf(t):return dict(location=vec(t.location),rotation=[float(t.rotation.pitch),float(t.rotation.yaw),float(t.rotation.roll)],matrix=t.get_matrix())
def matched(q,frame):
    while True:
        d=q.get(timeout=20)
        if d.frame==frame:return d
        if d.frame>frame:raise RuntimeError('Future sensor frame')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False,parents=True);(a.out/'clouds').mkdir();client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15';world=client.get_world();assert not any(x.type_id.startswith(('vehicle.','walker.','sensor.')) for x in world.get_actors());settings0=world.get_settings();weather0=world.get_weather();s=world.get_settings();s.synchronous_mode=True;s.fixed_delta_seconds=.05;s.substepping=True;s.max_substep_delta_time=.01;s.max_substeps=10;world.apply_settings(s);world.set_weather(carla.WeatherParameters.ClearNoon);actors=[];sensor=None;reports=[];begin=time.perf_counter()
    try:
        target=None;map0=world.get_map()
        for tr in map0.get_spawn_points():
            wp=map0.get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:target=ahead[0].transform;break
        assert target is not None;bp=world.get_blueprint_library();yaw=math.radians(target.rotation.yaw);forward=np.array([math.cos(yaw),math.sin(yaw)]);plane=target.location.z+.6
        plan=json.loads(Path(__file__).with_name('plan.json').read_text())
        for episode in plan:
                identifier=episode['blueprint'];angle=episode['yaw_deg']
                if identifier not in {x.id for x in bp}:
                    reports.append(dict(episode=episode,status='missing_blueprint'));continue
                delta=forward*episode['longitudinal_m']+np.array([-forward[1],forward[0]])*episode['lateral_m']
                spawn=carla.Transform(target.location+carla.Location(x=float(delta[0]),y=float(delta[1]),z=.05 if identifier.startswith('walker.') else .5),carla.Rotation(yaw=target.rotation.yaw+angle));actor=world.try_spawn_actor(bp.find(identifier),spawn)
                if actor is None:reports.append(dict(episode=episode,status='spawn_failed'));continue
                actors.append(actor)
                if identifier.startswith('vehicle.'):actor.apply_control(carla.VehicleControl(brake=1,hand_brake=True))
                for _ in range(30):world.tick(20)
                actor.set_simulate_physics(False)
                for layout,(lateral,height) in enumerate([(4.,8.),(8.,6.)]):
                    lidar=bp.find('sensor.lidar.ray_cast_semantic');attributes=dict(channels='256',range='35',points_per_second='2000000',rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0')
                    for k,v in attributes.items():lidar.set_attribute(k,v)
                    sensor=world.spawn_actor(lidar,carla.Transform(target.location+carla.Location(x=-forward[1]*lateral,y=forward[0]*lateral,z=height)));q=queue.Queue();sensor.listen(q.put)
                    for _ in range(3):frame=world.tick(20);matched(q,frame)
                    t=time.perf_counter();frame=world.tick(20);d=matched(q,frame);elapsed=time.perf_counter()-t;original_raw=np.frombuffer(d.raw_data,dtype=DTYPE);original_count=len(original_raw);raw=original_raw[::4].copy();matrix=np.asarray(d.transform.get_matrix());xyz=(np.c_[raw['x'],raw['y'],raw['z'],np.ones(len(raw))]@matrix.T)[:,:3];snap=world.get_snapshot();state=snap.find(actor.id);assert state is not None and snap.frame==frame;transform=actor.get_transform();bb=actor.bounding_box;center=transform.transform(carla.Location(*vec(bb.location)));key=episode['id']+'_v%d'%layout;file=a.out/'clouds'/(key+'.npz');np.savez_compressed(file,raw=raw,origin=np.asarray(vec(d.transform.location)),timestamp=d.timestamp,transform=matrix)
                    row=dict(id=key,episode=episode,road_yaw=target.rotation.yaw,status='captured',blueprint=identifier,klass='small' if identifier.startswith('walker.') else 'vehicle',angle=angle,layout=layout,frame=frame,sensor_frame=d.frame,snapshot_frame=snap.frame,timestamp=float(d.timestamp),snapshot_timestamp=float(snap.timestamp.elapsed_seconds),map=map0.name,query=vec(target.location)[:2],plane_z=plane,actor_id=actor.id,actor_transform=tf(transform),snapshot_transform=tf(state.get_transform()),center=vec(center),bounding_box=dict(location=vec(bb.location),rotation=[bb.rotation.pitch,bb.rotation.yaw,bb.rotation.roll],extent=vec(bb.extent),world_vertices=[vec(x) for x in bb.get_world_vertices(transform)]),velocity=vec(actor.get_velocity()),acceleration=vec(actor.get_acceleration()),sensor_transform=tf(d.transform),sensor_attributes=attributes,actor_semantic_tags=list(actor.semantic_tags),points=len(raw),original_points=original_count,sampling_stride=4,actor_returns=int(np.sum(raw['id']==actor.id)),acquisition_s=elapsed,cloud_file=str(file.relative_to(a.out)),cloud_sha256=hashlib.sha256(file.read_bytes()).hexdigest());reports.append(row);(a.out/'record.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps({k:row[k] for k in ['id','points','actor_returns','frame']}),flush=True);sensor.stop();sensor.destroy();sensor=None;world.tick(20)
                actor.destroy();actors.remove(actor);world.tick(20)
        (a.out/'record.json').write_text(json.dumps(reports,indent=2)+'\n');manifest=dict(host=socket.gethostname(),client_version=client.get_client_version(),server_version=client.get_server_version(),rows=len(reports),captured=sum(x['status']=='captured' for x in reports),elapsed_s=time.perf_counter()-begin,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plan_sha256=hashlib.sha256(Path(__file__).with_name('plan.json').read_bytes()).hexdigest(),model_sha256=hashlib.sha256(Path(__file__).with_name('model.py').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),scope='Fresh wider-position static episodes; every fourth original return retained. XYZ-only frontend; labels remain calibration/evaluation-only. Two sequential frozen-pose views, not dynamic closed loop or physical sensing validation.');(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    finally:
        if sensor:sensor.stop();sensor.destroy()
        for actor in actors:
            if actor.is_alive:actor.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(settings0);world.set_weather(weather0);(a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),walkers=len(world.get_actors().filter('walker.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')
if __name__=='__main__':main()
