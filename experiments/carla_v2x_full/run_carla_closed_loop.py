#!/usr/bin/env python3
"""Finite CARLA closed-loop validation using semantic-LiDAR evidence.

The normal controller never reads obstacle actor state. Actor state constructs the
scenario and evaluates clearance/collisions only. `full_info` receives current
sensor evidence without the software network and is explicitly an upper reference.
"""
import argparse, csv, hashlib, json, math, pathlib, queue, random, time
import carla
import numpy as np

from core import CONFIGS, METHODS, PROVIDER, REGIONS, deliver, effective_delay, fresh, select_messages


def get_frame(q, frame, timeout=10):
    deadline=time.perf_counter()+timeout;stale=0
    while True:
        item=q.get(timeout=max(.001,deadline-time.perf_counter()))
        if item.frame==frame:return item,stale
        if item.frame>frame:raise RuntimeError('semantic lidar frame %d ahead of requested %d'%(item.frame,frame))
        stale+=1


def straight_spawn(road_map):
    for candidate in road_map.get_spawn_points():
        wp=road_map.get_waypoint(candidate.location);ahead=wp.next(35)
        if not wp.is_junction and ahead and not ahead[0].is_junction:
            dyaw=(ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180
            if abs(dyaw)<3:return candidate
    raise RuntimeError('No straight non-junction spawn found')


def lane_waypoint(road_map, location, distance):
    wp=road_map.get_waypoint(location);remaining=distance
    while remaining>0:
        step=min(2.0,remaining);options=wp.next(step)
        if not options:raise RuntimeError('Route ended')
        wp=min(options,key=lambda x:abs((x.transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180));remaining-=step
    return wp


def sensor_state(measurement, ego_id, radius=6.5):
    points=0;objects=set();all_vehicle_points=0;all_vehicle_ids=set()
    for d in measurement:
        # CARLA 0.9.15's semantic-lidar Python proxy on this Windows-server /
        # Linux-client pair returns object_idx=0 if object_tag is accessed
        # first. Cache the instance id before any other detection property.
        # Non-zero ids identify dynamic actors; exclude the known ego id.
        object_idx=int(d.object_idx)
        if object_idx!=0 and object_idx!=int(ego_id):
            all_vehicle_points+=1;all_vehicle_ids.add(object_idx)
            p=d.point
            if p.x*p.x+p.y*p.y<=radius*radius:
                points+=1;objects.add(object_idx)
    return ('occupied' if points>=3 else 'free'),points,len(objects),all_vehicle_points,all_vehicle_ids


def steering(ego, road_map):
    loc=ego.get_location();tr=ego.get_transform();vel=ego.get_velocity();speed=math.sqrt(vel.x**2+vel.y**2+vel.z**2)
    wp=road_map.get_waypoint(loc);options=wp.next(max(4.0,speed*1.1));target=min(options,key=lambda w:abs((w.transform.rotation.yaw-tr.rotation.yaw+180)%360-180)) if options else wp
    dx=target.transform.location.x-loc.x;dy=target.transform.location.y-loc.y;heading=math.radians(tr.rotation.yaw);alpha=math.atan2(dy,dx)-heading;alpha=math.atan2(math.sin(alpha),math.cos(alpha))
    return float(np.clip(math.atan2(2*2.9*math.sin(alpha),max(4,math.hypot(dx,dy)))/.65,-1,1)),speed


def run_episode(client, world, method, config_name, scenario, seed, seconds, spawn, region_wps):
    bp=world.get_blueprint_library();road_map=world.get_map();config=CONFIGS[config_name];rng=random.Random(seed)
    actors=[];sensors=[];queues={};collisions=[];obstacle=None;rows=[]
    original=world.get_settings();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.no_rendering_mode=False;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings)
    try:
        ego_bp=bp.find('vehicle.tesla.model3');ego_bp.set_attribute('role_name','v2x_experiment_ego');ego=world.spawn_actor(ego_bp,spawn);actors.append(ego)
        collision=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=ego);sensors.append(collision);collision.listen(lambda e:collisions.append({'frame':e.frame,'other':e.other_actor.type_id}))
        if scenario=='hazard_a':
            tr=region_wps['A'].transform;tr.location.z+=.5;obp=bp.find('vehicle.audi.a2');obp.set_attribute('role_name','v2x_experiment_obstacle');obstacle=world.spawn_actor(obp,tr);actors.append(obstacle)
            # Keep normal physics so the server applies the requested spawn
            # transform on the first synchronous tick; an immediate
            # set_simulate_physics(False) freezes a fresh actor at its default
            # origin on this Windows build.
            world.tick(20)
            obstacle.apply_control(carla.VehicleControl(brake=1.0,hand_brake=True))
        for region in REGIONS:
            lidar_bp=bp.find('sensor.lidar.ray_cast_semantic')
            # Include the nadir ray: each sensor is mounted directly above the
            # decision region, so excluding -90 degrees would falsely label an
            # occupied region as free.
            for k,v in {'channels':'64','range':'30','points_per_second':'500000','rotation_frequency':'20','upper_fov':'10','lower_fov':'-90','sensor_tick':'0'}.items():lidar_bp.set_attribute(k,v)
            target=region_wps[region].transform;angle=math.radians(target.rotation.yaw)
            # Four metres to the side and eight metres high puts the lane ROI
            # near -63 degrees instead of at the lidar's singular nadir ray.
            loc=target.location+carla.Location(x=-math.sin(angle)*4,y=math.cos(angle)*4,z=8)
            sensor=world.spawn_actor(lidar_bp,carla.Transform(loc,carla.Rotation()),attach_to=None);sensors.append(sensor);q=queue.Queue();queues[region]=q;sensor.listen(q.put)
        for _ in range(10):
            f=world.tick(20)
            for q in queues.values():get_frame(q,f)
        sensor_transforms={r:str(sensors[1+i].get_transform()) for i,r in enumerate(REGIONS)}
        obstacle_transform_after_warmup=str(obstacle.get_transform()) if obstacle is not None else None
        evidence={};pending=[];go=False;first_go_after_clear=None;bytes_sent=scheduled=delivered_n=useful=drop=0;stale_frames=0;selection_counts={p.name:0 for p in PROVIDER.values()};cycle=0;clear_time=0.0 if scenario=='free' else 2.5;measured_start=time.perf_counter();prev_loc=ego.get_location();distance=0.0
        total_frames=int(round(seconds/.05))
        for step in range(total_frames):
            begin=time.perf_counter();sim_time=step*.05
            if obstacle is not None and scenario=='hazard_a' and sim_time>=clear_time:
                obstacle.destroy();actors.remove(obstacle);obstacle=None
            steer,speed=steering(ego,road_map)
            if go:
                throttle=float(np.clip(.4*(3.5-speed),0,.65));brake=float(np.clip(.4*(speed-3.5),0,1))
            else:
                throttle=0.0;brake=1.0
            ego.apply_control(carla.VehicleControl(throttle=throttle,brake=brake,steer=steer))
            frame=world.tick(20);tick_done=time.perf_counter();observations={};point_counts={};all_vehicle_counts={};seen_vehicle_ids={}
            for region,q in queues.items():
                data,stale=get_frame(q,frame);stale_frames+=stale;state,points,objects,all_points,all_ids=sensor_state(data,ego.id);observations[region]=state;point_counts[region]=points;all_vehicle_counts[region]=all_points;seen_vehicle_ids[region]=';'.join(map(str,sorted(all_ids)))
            if step%2==0:
                arrived_now=[x for x in pending if x[0]==cycle];pending=[x for x in pending if x[0]!=cycle]
                for _,name,observed,produced in arrived_now:
                    p=PROVIDER[name];before=evidence.get(p.region);evidence[p.region]=(observed,produced,name);delivered_n+=1
                    if before is None or before[0]!=observed or cycle-before[1]>config['ttl']:useful+=1
                if method=='full_info':
                    evidence={r:(observations[r],cycle,'full_info') for r in REGIONS};names=[]
                else:
                    names=select_messages(method,evidence,cycle,config);scheduled+=len(names);bytes_sent+=sum(PROVIDER[n].size for n in names)
                    for n in names:selection_counts[n]+=1
                    arrived=deliver(names,config,rng);drop+=len(names)-len(arrived)
                    for name in arrived:
                        p=PROVIDER[name];pending.append((cycle+effective_delay(p,config),name,observations[p.region],cycle))
                enough=all(fresh(evidence,r,cycle,config['ttl']) for r in REGIONS)
                go=enough and all(evidence[r][0]=='free' for r in REGIONS)
                if go and sim_time>=clear_time and first_go_after_clear is None:first_go_after_clear=sim_time
                cycle+=1
            loc=ego.get_location();distance+=loc.distance(prev_loc);prev_loc=loc;end=time.perf_counter()
            rows.append(dict(step=step,frame=frame,sim_time=sim_time,go=int(go),speed_mps=speed,x=loc.x,y=loc.y,distance_m=distance,obs_A=observations['A'],obs_B=observations['B'],points_A=point_counts['A'],points_B=point_counts['B'],all_vehicle_points_A=all_vehicle_counts['A'],all_vehicle_points_B=all_vehicle_counts['B'],seen_vehicle_ids_A=seen_vehicle_ids['A'],seen_vehicle_ids_B=seen_vehicle_ids['B'],evidence_A=evidence.get('A',('unknown',))[0],evidence_B=evidence.get('B',('unknown',))[0],bytes_sent=bytes_sent,loop_ms=(end-begin)*1000,tick_ms=(tick_done-begin)*1000,obstacle_present=int(obstacle is not None)))
        wall=time.perf_counter()-measured_start
        return dict(method=method,config=config_name,scenario=scenario,seed=seed,status='completed',sim_seconds=seconds,wall_seconds=wall,rtf=seconds/wall,distance_m=distance,clear_time=clear_time,first_go_after_clear=first_go_after_clear,clearance_to_go_s=(first_go_after_clear-clear_time if first_go_after_clear is not None else seconds-clear_time),wait_fraction=1-np.mean([r['go'] for r in rows]),bytes_sent=bytes_sent,scheduled_messages=scheduled,delivered_messages=delivered_n,useful_messages=useful,dropped_or_late_messages=drop,collisions=len(collisions),collision_events=json.dumps(collisions),loop_p95_ms=float(np.percentile([r['loop_ms'] for r in rows],95)),loop_p99_ms=float(np.percentile([r['loop_ms'] for r in rows],99)),loop_max_ms=max(r['loop_ms'] for r in rows),stale_sensor_frames=stale_frames,selection_counts=json.dumps(selection_counts,sort_keys=True),free_observation_fraction_A=np.mean([r['obs_A']=='free' for r in rows]),free_observation_fraction_B=np.mean([r['obs_B']=='free' for r in rows]),sensor_transforms=json.dumps(sensor_transforms),obstacle_transform_after_warmup=obstacle_transform_after_warmup),rows
    finally:
        for s in sensors:
            try:s.stop()
            except Exception:pass
        for a in reversed(sensors+actors):
            try:
                if a.is_alive:a.destroy()
            except Exception:pass
        world.apply_settings(original)


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',default='100.109.48.32');p.add_argument('--port',type=int,default=2000);p.add_argument('--seeds',type=int,default=5);p.add_argument('--seconds',type=float,default=5);p.add_argument('--methods',default=','.join(METHODS));p.add_argument('--configs',default='independent,contention');p.add_argument('--scenarios',default='free,hazard_a');p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'episodes').mkdir()
    client=carla.Client(a.host,a.port);client.set_timeout(30)
    if client.get_client_version()!=client.get_server_version():raise RuntimeError('CARLA client/server mismatch')
    world=client.get_world()
    if world.get_map().name.split('/')[-1]!='Town10HD_Opt':raise RuntimeError('Expected stable Town10HD_Opt, got '+world.get_map().name)
    if len(world.get_actors().filter('vehicle.*')):raise RuntimeError('Refusing to run with existing vehicles')
    spawn=straight_spawn(world.get_map());region_wps={'A':lane_waypoint(world.get_map(),spawn.location,15),'B':lane_waypoint(world.get_map(),spawn.location,30)}
    methods=tuple(x for x in a.methods.split(',') if x);configs=tuple(x for x in a.configs.split(',') if x);scenarios=tuple(x for x in a.scenarios.split(',') if x);summaries=[];started=time.time()
    for config in configs:
      for scenario in scenarios:
       for seed in range(a.seeds):
        for method in methods:
         print(json.dumps({'start':method,'config':config,'scenario':scenario,'seed':seed}),flush=True)
         derived=seed*1000003+list(configs).index(config)*101+list(scenarios).index(scenario)*17
         summary,frames=run_episode(client,world,method,config,scenario,derived,a.seconds,spawn,region_wps);summaries.append(summary)
         episode=a.out/'episodes'/('%s__%s__%s__%02d.csv'%(config,scenario,method,seed))
         with episode.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(frames[0]));w.writeheader();w.writerows(frames)
         with (a.out/'summary.partial.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    (a.out/'summary.partial.csv').replace(a.out/'summary.csv')
    manifest={'status':'completed','episodes':len(summaries),'seeds':a.seeds,'seconds':a.seconds,'methods':list(methods),'configs':list(configs),'scenarios':list(scenarios),'client_version':client.get_client_version(),'server_version':client.get_server_version(),'map':world.get_map().name,'started_unix':started,'finished_unix':time.time(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'core_sha256':hashlib.sha256(pathlib.Path(__file__).with_name('core.py').read_bytes()).hexdigest(),'limitations':['Controlled straight corridor, not natural traffic distribution','Two region sensor outputs are duplicated into two logical providers per region','Software link model, not PC5 measurement','Simple rule-based controller and semantic lidar, no learned perception']}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
