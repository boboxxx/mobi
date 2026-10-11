"""Finite nominal plant-capability reference, never an evidence safety grant."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback
import numpy as np

E=Path(__file__).parent
ROOT=E.resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments/actuator_admission_20261011'))
import model as M
R=M.R

def write(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def main():
    import carla
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    freeze=json.loads((E/'freeze.json').read_bytes())
    for section in ('sources','inputs'):
        for name,digest in freeze[section].items():assert R.sha(ROOT/name)==digest,name
    args.out.mkdir(parents=True,exist_ok=False);(args.out/'episodes').mkdir()
    context=json.loads((ROOT/'experiments/actuator_admission_20261011/context.json').read_bytes())
    plan=json.loads((E/'plan.json').read_bytes());write(args.out/'plan.json',plan)
    spec=importlib.util.spec_from_file_location('nominal_sampler',ROOT/'experiments/ego_actuator_realization_20261004/capture.py');sampling=importlib.util.module_from_spec(spec);spec.loader.exec_module(sampling)
    c=carla.Client('100.109.48.32',2000);c.set_timeout(30);w=c.get_world()
    assert c.get_client_version()==c.get_server_version()=='0.9.15' and w.get_map().name.endswith('Town10HD_Opt')
    assert not any(a.type_id.startswith(('vehicle.','walker.','sensor.')) for a in w.get_actors())
    original,weather=w.get_settings(),w.get_weather();s=w.get_settings();s.synchronous_mode=True;s.fixed_delta_seconds=.05;s.substepping=True;s.max_substep_delta_time=.01;s.max_substeps=10;w.apply_settings(s);w.set_weather(carla.WeatherParameters.ClearNoon)
    anchor=np.asarray(context['basis']['anchor']);road=np.asarray(context['basis']['road']);yaw=math.degrees(math.atan2(road[1,0],road[0,0]))
    owned=[];outcomes=[]
    try:
        for request in plan:
            rows=[];events=[];d=dict(request=request,rows=rows,collisions=events,scope='nominal simulation reference; no evidence-derived authorization')
            status='failed'
            try:
                bp=w.get_blueprint_library();pos=anchor+road@np.array([request['target_x_m'],5.4,.3])
                target=w.try_spawn_actor(bp.find(context['blueprint']),carla.Transform(carla.Location(*map(float,pos)),carla.Rotation(yaw=yaw)));assert target is not None;owned.append(target);target.apply_control(carla.WalkerControl(speed=0.))
                pos=anchor+road@np.array([-8.,0.,.5]);ego=w.try_spawn_actor(bp.find('vehicle.audi.a2'),carla.Transform(carla.Location(*map(float,pos)),carla.Rotation(yaw=yaw)));assert ego is not None;owned.append(ego)
                sensor=w.spawn_actor(bp.find('sensor.other.collision'),carla.Transform(),attach_to=ego);owned.append(sensor);sensor.listen(lambda e:events.append(dict(frame=e.frame,other=e.other_actor.type_id)))
                def command(t,b):
                    start=time.perf_counter_ns();control=carla.VehicleControl(throttle=t,brake=b,steer=0.,manual_gear_shift=True,gear=1)
                    res=c.apply_batch_sync([carla.command.ApplyVehicleControl(ego.id,control)],False);assert not any(r.error for r in res)
                    return (time.perf_counter_ns()-start+999)//1000
                for i in range(43):command(0.,1.);w.tick(20)
                refused=reached=False
                for step in range(830):
                    own=sampling.sample(w,ego,w.get_snapshot().frame);position=R.own_position(own,context['basis'])
                    domain=math.hypot(*own['velocity'][:2])<=.75 and -10000000<=position[0]<=6000000 and abs(position[1])<=500000
                    refused=refused or not domain or bool(events);reached=reached or position[0]>=3000000
                    go=3<=step<800 and not refused and not reached
                    throttle,brake=R.relay(own,go);fee=command(throttle,brake);frame=w.tick(20);after=sampling.sample(w,ego,frame)
                    refused=refused or math.hypot(*after['velocity'][:2])>.75
                    rows.append(dict(step=step,now_us=step*50000,own=own,after=after,go=go,reached=reached,refused=refused,domain_ok=domain,requested_throttle=throttle,requested_brake=brake,command_wall_fee_us=fee))
                status='captured'
            except Exception:d['exception']=traceback.format_exc()
            finally:
                for a in reversed(owned):
                    if a.type_id.startswith('sensor.'):a.stop()
                    a.destroy()
                owned=[];w.tick(20)
            d['status']=status;raw=(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode();p=args.out/'episodes'/(request['id']+'.json.gz');p.write_bytes(gzip.compress(raw,mtime=0))
            outcome=dict(id=request['id'],status=status,file=str(p.relative_to(args.out)),sha256=R.sha(p),logical_sha256=hashlib.sha256(raw).hexdigest());outcomes.append(outcome);write(args.out/'outcomes.json',outcomes);print(json.dumps(outcome),flush=True)
    finally:
        for a in reversed(owned):
            if a.type_id.startswith('sensor.'):a.stop()
            a.destroy()
        w.apply_settings(original);w.set_weather(weather);write(args.out/'cleanup.json',dict(vehicles=len(w.get_actors().filter('vehicle.*')),walkers=len(w.get_actors().filter('walker.*')),sensors=len(w.get_actors().filter('sensor.*')),synchronous=w.get_settings().synchronous_mode))

if __name__=='__main__':main()
