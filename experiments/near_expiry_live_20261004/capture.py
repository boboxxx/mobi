#!/usr/bin/env python3
"""Finite causal measured-delay simulation; production authorizations stay false."""
import gzip,json,math,queue,time,traceback
from pathlib import Path
import carla
import numpy as np
import runtime as R
import sys
sys.path.insert(0,str(R.ROOT/'experiments/ego_actuator_realization_20261004'))
# Load the frozen physical sampler by exact path.
import importlib.util
spec=importlib.util.spec_from_file_location('fixed_ego_sample',R.ROOT/'experiments/ego_actuator_realization_20261004/capture.py');sampling=importlib.util.module_from_spec(spec);spec.loader.exec_module(sampling)
E=Path(__file__).resolve().parent;P=R.ROOT/'results'/E.name
DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n')
def matched(q,frame):
 while True:
  d=q.get(timeout=20)
  if d.frame==frame:return d
  assert d.frame<frame
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 f=json.loads((E/'freeze.json').read_bytes())
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert R.sha(R.ROOT/n)==h,n
 a.out.mkdir(parents=True,exist_ok=False);(a.out/'clouds').mkdir();(a.out/'packets').mkdir();(a.out/'episodes').mkdir()
 plan=json.loads((E/'plan.json').read_bytes());write(a.out/'plan.json',plan)
 parent=json.loads((R.ROOT/'results/prospective_component_20261004/qualification_test_sheng.json').read_bytes())
 ctx={k:parent[k] for k in ('catalog','basis','registry')};ctx.update(action_us=R.ACTION,speed_cap_um_s=750000,new_policy_qualified=False)
 write(a.out/'context.json',ctx);models=R.load_models();background=json.loads((R.ROOT/'results/background_frontend_20261004/background.json').read_bytes())
 client=carla.Client('100.109.48.32',2000);client.set_timeout(30);world=client.get_world()
 assert client.get_client_version()==client.get_server_version()=='0.9.15' and world.get_map().name.endswith('Town10HD_Opt')
 assert not any(x.type_id.startswith(('vehicle.','walker.','sensor.')) for x in world.get_actors())
 original,weather=world.get_settings(),world.get_weather();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings);world.set_weather(carla.WeatherParameters.ClearNoon)
 owned=[];sensor=None;outcomes=[];start=time.perf_counter()
 try:
  basis=ctx['basis'];anchor=np.array(basis['anchor']);road=np.array(basis['road']);yaw=math.degrees(math.atan2(road[1,0],road[0,0]));library=world.get_blueprint_library()
  for request in plan:
   rows=[];sources=[];events=[];outcome=dict(request=request,status='failed');record=dict(request=request,rows=rows,sources=sources)
   try:
    target=world.try_spawn_actor(library.find(request['blueprint']),carla.Transform(carla.Location(*[float(v) for v in anchor+np.array([0.,0.,.05 if request['blueprint'].startswith('walker.') else .5])]),carla.Rotation(yaw=yaw)))
    assert target is not None;owned.append(target)
    if target.type_id.startswith('vehicle.'):target.apply_control(carla.VehicleControl(brake=1.,hand_brake=True))
    pos=anchor+road@np.array([float(request['start_x_m']),0.,.5]);ego=world.try_spawn_actor(library.find('vehicle.audi.a2'),carla.Transform(carla.Location(*[float(v) for v in pos]),carla.Rotation(yaw=yaw)))
    assert ego is not None;owned.append(ego)
    collision=world.spawn_actor(library.find('sensor.other.collision'),carla.Transform(),attach_to=ego);owned.append(collision);collision.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
    body=dict(extent=sampling.vec(ego.bounding_box.extent),offset=sampling.vec(ego.bounding_box.location),rotation=[ego.bounding_box.rotation.pitch,ego.bounding_box.rotation.yaw,ego.bounding_box.rotation.roll]);record['body']=body
    assert sampling.vec(target.bounding_box.extent)==ctx['catalog'][request['blueprint']]
    def command(throttle,brake):
     c=carla.VehicleControl(throttle=throttle,brake=brake,steer=0.,manual_gear_shift=True,gear=1)
     response=client.apply_batch_sync([carla.command.ApplyVehicleControl(ego.id,c)],False);assert not any(v.error for v in response)
    for _ in range(40):command(0.,1.);world.tick(20)
    bp=library.find('sensor.lidar.ray_cast_semantic')
    attrs=dict(channels='256',range='35',points_per_second='2000000',rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0')
    for k,v in attrs.items():bp.set_attribute(k,v)
    pos=anchor+road@np.array([0.,4.,8.]);sensor=world.spawn_actor(bp,carla.Transform(carla.Location(*[float(v) for v in pos])));q=queue.Queue();sensor.listen(q.put)
    for _ in range(3):
     before=time.perf_counter_ns();frame=world.tick(20);d=matched(q,frame);acquisition=(time.perf_counter_ns()-before+999)//1000
    cache=None;pending=[];ready=[];free=0;cache_id=None
    record.update(ego_id=ego.id,target_id=target.id,sensor_attributes=attrs)
    for step in range(200):
     frame=world.get_snapshot().frame;own=sampling.sample(world,ego,frame);source_us=math.floor(own['timestamp']*1e6);assert d.frame==frame
     tr=target.get_transform();center=tr.transform(carla.Location(*sampling.vec(target.bounding_box.location)))
     truth=dict(frame=frame,center=sampling.vec(center),vertices=[sampling.vec(v) for v in target.bounding_box.get_world_vertices(tr)],velocity=sampling.vec(target.get_velocity()))
     if step<160:
      before=time.perf_counter_ns();raw=np.frombuffer(d.raw_data,dtype=DTYPE)[::4].copy();T=np.array(d.transform.get_matrix());copy_us=(time.perf_counter_ns()-before+999)//1000
      before=time.perf_counter_ns();wire,meta=R.encode(raw,T,own,body,ctx,request['blueprint'],request['method'],source_us,frame,models,background);source_fee=(time.perf_counter_ns()-before+999)//1000+copy_us
      cloud=request['id']+'_s%03d.npz'%step;packet=request['id']+'_s%03d.bin'%step
      np.savez_compressed(a.out/'clouds'/cloud,raw=raw,transform=T,timestamp=d.timestamp)
      (a.out/'packets'/packet).write_bytes(wire)
      arrival,free=R.source_link(source_us,acquisition,source_fee,len(wire),request['propagation_us'],free)
      dropped=30<=step<50
      item=dict(step=step,source_us=source_us,frame=frame,acquisition_us=acquisition,source_fee_us=source_fee,wire_bytes=len(wire),cloud=cloud,cloud_sha256=R.sha(a.out/'clouds'/cloud),packet=packet,packet_sha256=R.sha(a.out/'packets'/packet),arrival_us=arrival,tx_free_us=free,dropped=dropped,own=own,truth=truth,meta=meta)
      sources.append(item);pending.append((item,wire))
     deliveries=[]
     while pending and pending[0][0]['arrival_us']<=source_us:
      item,wire=pending.pop(0)
      if item['dropped']:item.update(receiver_fee_us=0,ready_us=None);continue
      before=time.perf_counter_ns();decoded=R.decode(wire,ctx);fee=(time.perf_counter_ns()-before+999)//1000;available=source_us+R.roundup(max(1,fee));item.update(receiver_fee_us=fee,ready_us=available,decode_at_us=source_us)
      ready.append((available,item['step'],decoded));deliveries.append(item['step'])
     while ready and ready[0][0]<=source_us:
      _,cache_id,cache=ready.pop(0)
     before=time.perf_counter_ns();proposal,gate=R.choose(cache,own,body,ctx,source_us);query_fee=(time.perf_counter_ns()-before+999)//1000
     if proposal is not None:
      domain=gate['query_domain_valid'];gate=R.decision(proposal,source_us+query_fee,R.ACTION);gate['query_domain_valid']=domain;gate['geometry_eligible']&=domain
     qq=R.query_position(own,basis);speed=math.hypot(*own['velocity'][:2]);odom_ok=(speed<=.6 and -10000000<=qq[0]<=-3000000 and abs(qq[1])<=500000)
     engineering_go=step<160 and gate['geometry_eligible'] and odom_ok
     throttle,brake=R.relay(own,engineering_go);command(throttle,brake)
     before=time.perf_counter_ns();next_frame=world.tick(20);d=matched(q,next_frame);acquisition=(time.perf_counter_ns()-before+999)//1000
     after=sampling.sample(world,ego,next_frame)
     rows.append(dict(step=step,now_us=source_us,own=own,after=after,truth=truth,cache_source_step=cache_id,query_fee_us=query_fee,proposal=proposal,gate=gate,odom_ok=odom_ok,engineering_go=engineering_go,requested_throttle=throttle,requested_brake=brake,deliveries=deliveries))
    record['pending_at_end']=[i['step'] for i,w in pending];record['receiver_pending_at_end']=[i for t,i,o in ready]
    outcome['status']='captured'
   except Exception:record['exception']=traceback.format_exc();outcome['reason']='capture_exception'
   finally:
    if sensor is not None:sensor.stop();sensor.destroy();sensor=None
    for actor in reversed(owned):
     if actor.type_id.startswith('sensor.'):actor.stop()
     actor.destroy()
    owned=[];world.tick(20)
   record['collisions']=list(events);record['outcome']=dict(outcome)
   logical=(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();file=a.out/'episodes'/(request['id']+'.json.gz');file.write_bytes(gzip.compress(logical,mtime=0))
   outcome.update(file=str(file.relative_to(a.out)),sha256=R.sha(file),logical_sha256=__import__('hashlib').sha256(logical).hexdigest(),logical_bytes=len(logical),decisions=len(rows),sources=len(sources));outcomes.append(outcome);write(a.out/'outcomes.json',outcomes)
   print(json.dumps(dict(id=request['id'],status=outcome['status'],decisions=len(rows),sources=len(sources),elapsed_s=time.perf_counter()-start)),flush=True)
  write(a.out/'manifest.json',dict(planned=len(plan),captured=sum(v['status']=='captured' for v in outcomes),freeze_sha256=R.sha(E/'freeze.json'),elapsed_s=time.perf_counter()-start,scope='Fresh physical unqualified ego measured-delay co-simulation, no statistical/radio/WCET guarantee.',goal_complete=False))
 finally:
  if sensor is not None:sensor.stop();sensor.destroy()
  for actor in reversed(owned):actor.destroy()
  if world.get_settings().synchronous_mode:world.tick(20)
  world.apply_settings(original);world.set_weather(weather)
  write(a.out/'cleanup.json',dict(vehicles=len(world.get_actors().filter('vehicle.*')),walkers=len(world.get_actors().filter('walker.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode))
if __name__=='__main__':main()
