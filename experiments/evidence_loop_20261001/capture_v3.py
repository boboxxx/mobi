#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,queue,socket,sys,time
from pathlib import Path
import numpy as np
import carla
from control import TickControl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_evidence_20261001'))
import body
from compress import pack as compressed_pack
from fast_path import renew
from fast_path import Receiver
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'actuation_calibration_20261001'))
from capture_3d import sample
from model import SCALES
DTYPE=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('cos','<f4'),('id','<u4'),('tag','<u4')])


def matched(q,frame):
    while True:
        d=q.get(timeout=20)
        if d.frame==frame:return d
        if d.frame>frame:raise RuntimeError('Future sensor frame')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='100.109.48.32');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2];model_path=root/'results/actuation_calibration_20261001/analysis/models.json';model=json.loads(model_path.read_text())['constant'];bound=np.maximum([0,0,0,.05],np.array(model['weights'])[0])+model['q']*SCALES
    client=carla.Client(a.host,2000);client.set_timeout(30);assert client.get_client_version()==client.get_server_version()=='0.9.15';world=client.get_world();assert not len(world.get_actors().filter('vehicle.*'))
    original=world.get_settings();weather=world.get_weather();settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.05;settings.substepping=True;settings.max_substep_delta_time=.01;settings.max_substeps=10;world.apply_settings(settings);world.set_weather(carla.WeatherParameters.ClearNoon)
    sensor=vehicle=collision=None;bp=world.get_blueprint_library();reports=[];begin_all=time.perf_counter()
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    try:
        target=None
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:target=ahead[0].transform;break
        assert target is not None;yaw=math.radians(target.rotation.yaw);forward=np.array([math.cos(yaw),math.sin(yaw)])
        for layout,(lateral,height) in enumerate([(4.,8.),(8.,6.)]):
          for use_history in [False,True]:
            name='view%d_%s'%(layout,'history' if use_history else 'current');out=a.out/name;out.mkdir();(out/'clouds').mkdir();(out/'packets').mkdir()
            control=TickControl(bound);receiver=Receiver(profiles,contract,name,world.get_map().name);events=[];tick_rows=[];decisions=[];seq=0;template=None
            lidar=bp.find('sensor.lidar.ray_cast_semantic')
            for k,v in dict(channels='256',range='35',points_per_second='2000000',rotation_frequency='20',upper_fov='10',lower_fov='-90',sensor_tick='0').items():lidar.set_attribute(k,v)
            sensor=world.spawn_actor(lidar,carla.Transform(target.location+carla.Location(x=-forward[1]*lateral,y=forward[0]*lateral,z=height)));q=queue.Queue();sensor.listen(q.put)
            def tick():
                if vehicle:
                    throttle,brake,why=control.command(world.get_snapshot().frame)
                    r=client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,carla.VehicleControl(throttle=throttle,brake=brake,steer=0.))],False);assert not any(x.error for x in r)
                frame=world.tick(20);d=matched(q,frame)
                if vehicle:
                    st=sample(world,vehicle,frame);control.observe(st);tick_rows.append(dict(command_throttle=throttle,command_brake=brake,reason=why,breach=control.breach,**st))
                return d
            for _ in range(3):tick()
            def process(phase,index,drop=False):
                nonlocal seq,template
                start=time.perf_counter();d=tick();raw=np.frombuffer(d.raw_data,dtype=DTYPE);xyz=(np.column_stack([raw['x'],raw['y'],raw['z'],np.ones(len(raw))])@np.asarray(d.transform.get_matrix()).T)[:,:3];origin=np.array([d.transform.location.x,d.transform.location.y,d.transform.location.z]);acq=time.perf_counter()-start
                st=sample(world,vehicle) if vehicle else None;query=(st['x'],st['y']) if st else (target.location.x,target.location.y);angle=math.radians(st['yaw']) if st else yaw
                scope=body.Scope(name,world.get_map().name,query,target.location.z+.6);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=angle,acceleration=0.,yaw_rate=0.)
                prior=receiver.latest_region() if use_history else None
                if prior and not prior.established<=d.timestamp<prior.expires:prior=None
                start=time.perf_counter();blob=renew(template,xyz,origin,d.timestamp,d.timestamp,profiles,scope,contract,motion,prior,horizon=.4,sequence=seq) if template else None;source_mode='renew' if blob else 'compressed'
                if blob is None:blob=compressed_pack(xyz,origin,d.timestamp,d.timestamp,profiles,scope,contract,motion,prior,horizon=.4,sequence=seq)
                if blob:template=blob
                generation=time.perf_counter()-start
                start=time.perf_counter();accepted=bool(blob and not drop and receiver.accept(blob,scope,motion,d.timestamp+.02));verification=time.perf_counter()-start
                delay_ticks=max(1,math.ceil((acq+generation+verification+.02)/.05))
                if delay_ticks>200:raise RuntimeError('Single computation exceeds finite delay limit')
                for _ in range(delay_ticks):tick()
                now=world.get_snapshot().timestamp.elapsed_seconds;region=receiver.latest_region() if accepted else None;available=bool(region and now<region.expires);root_ready=bool(available and now+.05<region.expires)
                state=sample(world,vehicle) if vehicle else None;issued=bool(phase=='drive' and available and control.issue(region,state,state['frame'],now))
                key='%s_%03d'%(phase,index);np.savez_compressed(out/'clouds'/(key+'.npz'),xyz=xyz,origin=origin,timestamp=d.timestamp,query=query,plane_z=scope.plane_z)
                if blob:(out/'packets'/(key+'.json')).write_bytes(blob)
                row=dict(id=key,source_mode=source_mode,receiver_check_time=d.timestamp+.02,phase=phase,index=index,sequence=seq,frame=d.frame,stamp=d.timestamp,now=now,yaw=angle,query=list(query),prior=prior.identity if prior else None,packet_sha256=hashlib.sha256(blob).hexdigest() if blob else None,packet_bytes=len(blob) if blob else 0,geometry=blob is not None,dropped=drop,receiver_accepted=accepted,available=available,root_ready=root_ready,issued=issued,breach=control.breach,acquisition_s=acq,generation_s=generation,verification_s=verification,modeled_link_s=.02,delay_ticks=delay_ticks,decision_state=state)
                decisions.append(row);seq+=1;return root_ready if phase=='root' else available
            initialized=False
            for i in range(3):
                if process('root',i):initialized=True;break
            if initialized:
                spawn=carla.Transform(target.location+carla.Location(z=.5),target.rotation);vehicle=world.spawn_actor(bp.find('vehicle.audi.a2'),spawn);collision=world.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=vehicle);collision.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
                for i in range(20):process('warm',i)
                initial=sample(world,vehicle)
                for i in range(40):
                    process('drive',i,20<=i<=24)
                    if i%10==9:print(json.dumps(dict(run=name,step=i,issued=control.issued,breach=control.breach)),flush=True)
                # Flush the final finite backup through at least 40 ticks.
                for _ in range(40):tick()
                final=sample(world,vehicle);progress=float(np.dot([final['x']-initial['x'],final['y']-initial['y']],forward))
            else:initial=final=None;progress=0.
            record=dict(run=name,layout=layout,history=use_history,initialized=initialized,initial=initial,final=final,progress_m=progress,issued=control.issued,breach=control.breach,collisions=list(events),decisions=decisions,ticks=tick_rows,statistical_coverage_claimed=False,physical_movement_authorized=False)
            (out/'record.json.gz').write_bytes(gzip.compress(json.dumps(record,separators=(',',':')).encode(),mtime=0));reports.append({k:record[k] for k in ['run','layout','history','initialized','progress_m','issued','breach','collisions']});(a.out/'summary.json').write_text(json.dumps(reports,indent=2)+'\n')
            if collision:collision.stop();collision.destroy();collision=None
            if vehicle:vehicle.destroy();vehicle=None
            sensor.stop();sensor.destroy();sensor=None;world.tick(20);print(json.dumps(reports[-1]),flush=True)
        deps={}
        for mod in list(sys.modules.values()):
            f=getattr(mod,'__file__',None)
            if f:
                p=Path(f).resolve()
                if p.is_file() and root in p.parents and p.suffix=='.py':deps[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
        manifest=dict(host=socket.gethostname(),source_sha256=deps,addendum_sha256=hashlib.sha256(Path(__file__).with_name('FAST_PATH_FOLLOWUP.md').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),model_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),bound=bound.tolist(),runs=len(reports),elapsed_s=time.perf_counter()-begin_all,scope='Actual ego controls with measured-delay synchronous co-simulation; controlled pre-ego raw-ray initialization; no real-time or statistical deployment guarantee.')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    finally:
        for actor in [collision,sensor,vehicle]:
            if actor and actor.is_alive:
                if actor.type_id.startswith('sensor.'):actor.stop()
                actor.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original);world.set_weather(weather);(a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
