#!/usr/bin/env python3
"""Finite physical moving-actor scan families; labels are capture/audit only."""
import argparse,hashlib,json,math,queue,socket,time
from pathlib import Path
import numpy as np
import carla
DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(v):return [float(v.x),float(v.y),float(v.z)]
def tf(t):return dict(location=vec(t.location),rotation=[float(t.rotation.pitch),float(t.rotation.yaw),float(t.rotation.roll)],matrix=t.get_matrix())
def matched(q,frame):
    while True:
        d=q.get(timeout=20)
        if d.frame==frame:return d
        if d.frame>frame:raise RuntimeError('Future sensor frame')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(exist_ok=False,parents=True);(a.out/'clouds').mkdir()
    client=carla.Client(a.host,2000);client.set_timeout(30)
    assert client.get_client_version()==client.get_server_version()=='0.9.15'
    world=client.get_world();assert not any(x.type_id.startswith(('vehicle.','walker.','sensor.')) for x in world.get_actors())
    settings0=world.get_settings();weather0=world.get_weather();settings=world.get_settings()
    settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10
    world.apply_settings(settings);world.set_weather(carla.WeatherParameters.ClearNoon)
    owned=[];sensors=[];reports=[];episode_reports=[];begin=time.perf_counter()
    try:
        target=None;map0=world.get_map()
        for tr in map0.get_spawn_points():
            wp=map0.get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:target=ahead[0].transform;break
        assert target is not None
        library=world.get_blueprint_library();yaw=math.radians(target.rotation.yaw);forward=np.array([math.cos(yaw),math.sin(yaw)]);lateral=np.array([-forward[1],forward[0]])
        for ep in json.loads((HERE/'plan.json').read_bytes()):
            identifier=ep['blueprint'];angle=ep['yaw_deg'];delta=forward*ep['longitudinal_m']+lateral*ep['lateral_m']
            if identifier not in {x.id for x in library}:
                episode_reports.append(dict(episode=ep,status='missing_blueprint'));continue
            spawn=carla.Transform(target.location+carla.Location(x=float(delta[0]),y=float(delta[1]),z=.05 if identifier.startswith('walker.') else .5),carla.Rotation(yaw=target.rotation.yaw+angle))
            actor=world.try_spawn_actor(library.find(identifier),spawn)
            if actor is None:
                episode_reports.append(dict(episode=ep,status='spawn_failed'));continue
            owned.append(actor)
            if identifier.startswith('vehicle.'):actor.apply_control(carla.VehicleControl(brake=1,hand_brake=True))
            for _ in range(30):world.tick(20)
            for layout,(offset,height) in enumerate([(4.,8.),(8.,6.)]):
                bp=library.find('sensor.lidar.ray_cast_semantic');attributes=dict(channels='256',range='35',points_per_second='2000000',rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0')
                for k,v in attributes.items():bp.set_attribute(k,v)
                sensor=world.spawn_actor(bp,carla.Transform(target.location+carla.Location(x=float(lateral[0]*offset),y=float(lateral[1]*offset),z=height)))
                q=queue.Queue();sensor.listen(q.put);sensors.append((sensor,q,layout))
            for _ in range(3):
                frame=world.tick(20)
                for sensor,q,layout in sensors:matched(q,frame)
            heading=yaw+math.radians(angle);direction=carla.Vector3D(x=math.cos(heading),y=math.sin(heading),z=0);speed=ep['target_speed_mps']
            if identifier.startswith('vehicle.'):actor.apply_control(carla.VehicleControl(brake=0,hand_brake=False))
            trajectory=[]
            for step in range(21):
                if identifier.startswith('walker.'):actor.apply_control(carla.WalkerControl(direction=direction,speed=speed,jump=False))
                else:actor.set_target_velocity(carla.Vector3D(x=direction.x*speed,y=direction.y*speed,z=0))
                start=time.perf_counter();frame=world.tick(20);packets=[]
                for sensor,q,layout in sensors:packets.append((sensor,matched(q,frame),layout,time.perf_counter()-start))
                snap=world.get_snapshot();state=snap.find(actor.id);assert state is not None and snap.frame==frame
                transform=actor.get_transform();bb=actor.bounding_box;center=transform.transform(carla.Location(*vec(bb.location)))
                truth=dict(step=step,frame=frame,timestamp=float(snap.timestamp.elapsed_seconds),center=vec(center),actor_transform=tf(transform),snapshot_transform=tf(state.get_transform()),velocity=vec(actor.get_velocity()),acceleration=vec(actor.get_acceleration()),world_vertices=[vec(v) for v in bb.get_world_vertices(transform)])
                trajectory.append(truth)
                if step not in (0,5,10):continue
                for sensor,d,layout,acquisition in packets:
                    assert d.frame==frame
                    original=np.frombuffer(d.raw_data,dtype=DTYPE);selection_begin=time.perf_counter();raw=original[::4].copy();selection_s=time.perf_counter()-selection_begin;key=ep['id']+'_s%02d_v%d'%(step,layout);file=a.out/'clouds'/(key+'.npz')
                    np.savez_compressed(file,raw=raw,origin=np.asarray(vec(d.transform.location)),timestamp=d.timestamp,transform=np.asarray(d.transform.get_matrix()))
                    reports.append(dict(id=key,episode_id=ep['id'],blueprint=identifier,split=ep['split'],step=step,layout=layout,road_yaw=target.rotation.yaw,query=vec(target.location)[:2],frame=frame,sensor_frame=d.frame,timestamp=float(d.timestamp),snapshot_timestamp=float(snap.timestamp.elapsed_seconds),actor_id=actor.id,center=vec(center),sensor_transform=tf(d.transform),sensor_attributes=attributes,bounding_box=dict(location=vec(bb.location),rotation=[bb.rotation.pitch,bb.rotation.yaw,bb.rotation.roll],extent=vec(bb.extent)),points=len(raw),original_points=len(original),sampling_stride=4,actor_returns=int(np.sum(raw['id']==actor.id)),acquisition_s=acquisition,selection_s=selection_s,cloud_file=str(file.relative_to(a.out)),cloud_sha256=sha(file)))
            episode_reports.append(dict(episode=ep,status='captured',actor_id=actor.id,trajectory=trajectory,bounding_box=dict(location=vec(bb.location),extent=vec(bb.extent)),map=map0.name))
            for sensor,q,layout in sensors:sensor.stop();sensor.destroy()
            sensors=[];actor.destroy();owned.remove(actor);world.tick(20)
            if len(episode_reports)%10==0:
                (a.out/'record.json').write_text(json.dumps(reports,indent=2)+'\n');(a.out/'episodes.json').write_text(json.dumps(episode_reports,indent=2)+'\n')
                print(json.dumps(dict(episodes=len(episode_reports),frames=len(reports),elapsed_s=time.perf_counter()-begin)),flush=True)
        (a.out/'record.json').write_text(json.dumps(reports,indent=2)+'\n');(a.out/'episodes.json').write_text(json.dumps(episode_reports,indent=2)+'\n')
        manifest=dict(host=socket.gethostname(),client_version=client.get_client_version(),server_version=client.get_server_version(),episodes=len(episode_reports),captured_episodes=sum(e['status']=='captured' for e in episode_reports),frames=len(reports),stored_rays=sum(r['points'] for r in reports),original_reported_rays=sum(r['original_points'] for r in reports),elapsed_s=time.perf_counter()-begin,source_sha256=sha(Path(__file__)),plan_sha256=sha(HERE/'plan.json'),protocol_sha256=sha(HERE/'PROTOCOL.md'),scope='Fresh moving physical actors, six sampled per-frame scans and21 truth snapshots per captured episode. No ego control; finite causal-trace study, not wall-clock live safety.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
    finally:
        for sensor,q,layout in sensors:
            if sensor.is_alive:sensor.stop();sensor.destroy()
        for actor in owned:
            if actor.is_alive:actor.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(settings0);world.set_weather(weather0)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),walkers=len(world.get_actors().filter('walker.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')
if __name__=='__main__':main()
