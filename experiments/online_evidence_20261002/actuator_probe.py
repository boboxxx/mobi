#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,socket,sys
from pathlib import Path
import numpy as np
import carla
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'actuation_calibration_20261001'))
from capture_3d import sample


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    client=carla.Client('100.109.48.32',2000);client.set_timeout(30);world=client.get_world();assert client.get_client_version()==client.get_server_version()=='0.9.15'
    assert len(world.get_actors().filter('vehicle.*'))==len(world.get_actors().filter('sensor.*'))==0
    original=world.get_settings();weather=world.get_weather();s=world.get_settings();s.synchronous_mode=True;s.fixed_delta_seconds=.05;s.substepping=True;s.max_substep_delta_time=.01;s.max_substeps=10;world.apply_settings(s);world.set_weather(carla.WeatherParameters.ClearNoon)
    vehicle=collision=None;reports=[]
    try:
        target=None
        for tr in world.get_map().get_spawn_points():
            wp=world.get_map().get_waypoint(tr.location);ahead=wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction and abs((ahead[0].transform.rotation.yaw-wp.transform.rotation.yaw+180)%360-180)<3:target=ahead[0].transform;break
        assert target is not None;angle=math.radians(target.rotation.yaw);forward=np.array([math.cos(angle),math.sin(angle)])
        for repeat in range(4):
            for go_ticks in [1,2,4,8]:
                for mode in (['automatic','manual1'] if repeat%2==0 else ['manual1','automatic']):
                    manual=mode=='manual1';name='%s_go%d_r%d'%(mode,go_ticks,repeat);events=[];rows=[]
                    vehicle=world.spawn_actor(world.get_blueprint_library().find('vehicle.audi.a2'),carla.Transform(target.location+carla.Location(z=.5),target.rotation))
                    collision=world.spawn_actor(world.get_blueprint_library().find('sensor.other.collision'),carla.Transform(),attach_to=vehicle);collision.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
                    pc=vehicle.get_physics_control();config={k:getattr(pc,k,None) for k in ['use_gear_autobox','gear_switch_time','clutch_strength','max_rpm']}
                    def tick(throttle,brake):
                        control=carla.VehicleControl(throttle=throttle,brake=brake,steer=0.,manual_gear_shift=manual,gear=1 if manual else 0)
                        response=client.apply_batch_sync([carla.command.ApplyVehicleControl(vehicle.id,control)],False);assert not any(x.error for x in response)
                        frame=world.tick(20);state=sample(world,vehicle,frame);actual=vehicle.get_control();state.update(gear=actual.gear,manual_gear_shift=actual.manual_gear_shift,requested_throttle=throttle,requested_brake=brake);rows.append(state)
                    for _ in range(15):tick(0.,1.)
                    initial=rows[-1].copy();assert initial['speed']<.02
                    for _ in range(go_ticks):tick(.45,0.)
                    go_end=rows[-1].copy()
                    for _ in range(40):tick(0.,1.)
                    final=rows[-1];progress=float(np.dot([final['x']-initial['x'],final['y']-initial['y']],forward));go_progress=float(np.dot([go_end['x']-initial['x'],go_end['y']-initial['y']],forward))
                    report=dict(name=name,mode=mode,go_ticks=go_ticks,repeat=repeat,progress_m=progress,go_progress_m=go_progress,peak_speed=max(st['speed'] for st in rows[15:]),final_speed=final['speed'],collision_count=len(events),gearbox=config)
                    record=dict(summary=report,initial=initial,go_end=go_end,rows=rows,collisions=events)
                    (a.out/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(record,separators=(',',':')).encode(),mtime=0));reports.append(report);(a.out/'summary.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(report),flush=True)
                    collision.stop();collision.destroy();collision=None;vehicle.destroy();vehicle=None;world.tick(20)
        root=Path(__file__).resolve().parents[2];deps={}
        for mod in list(sys.modules.values()):
            file=getattr(mod,'__file__',None)
            if file:
                p=Path(file).resolve()
                if p.is_file() and root in p.parents and p.suffix=='.py':deps[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
        (a.out/'manifest.json').write_text(json.dumps(dict(host=socket.gethostname(),source_sha256=deps,protocol_sha256=hashlib.sha256(Path(__file__).with_name('ACTUATOR_PROTOCOL.md').read_bytes()).hexdigest(),episodes=len(reports),scope='Post-analysis actuator component diagnostic; manual policy not calibrated for evidence control.'),indent=2)+'\n')
    finally:
        for actor in [collision,vehicle]:
            if actor:
                if actor.type_id.startswith('sensor.'):actor.stop()
                actor.destroy()
        if world.get_settings().synchronous_mode:world.tick(20)
        world.apply_settings(original);world.set_weather(weather)
        (a.out/'cleanup.json').write_text(json.dumps(dict(vehicles=len(world.get_actors().filter('vehicle.*')),sensors=len(world.get_actors().filter('sensor.*')),synchronous=world.get_settings().synchronous_mode),indent=2)+'\n')


if __name__=='__main__':main()
