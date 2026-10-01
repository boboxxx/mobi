#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import numpy as np
from body import *
from renew import renew
from stopping import admit,Stopping
from history import Receiver
from run_probe import profiles
from run_study import write


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir()
    frames={r['id']:r for r in csv.DictReader((a.capture/'frames.csv').open())};rows=[];p=profiles();c=Contract()
    for ordinal,path in enumerate(sorted((a.capture/'clouds').glob('*.npz'))):
        density,layout,scenario,step=path.stem.split('_')
        if scenario=='free' and step=='00':continue
        d=np.load(path);q=d['query'];origin=d['origin'];lat=origin[:2]-q;yaw=math.atan2(-lat[0],lat[1]);scope=Scope('body-renew:'+density+':'+layout+':'+scenario,'Town10HD_Opt/world',tuple(q),float(d['probe_z']));stamp=2.+ordinal*.05
        for speed in [0.,.5,1.]:
          m=Motion(acceleration=8.,vx=speed*math.cos(yaw),vy=speed*math.sin(yaw),yaw=yaw)
          for h in [.2,.4,.6]:
            template=a.reference/'packets'/('%s_%s_free_00_v%s_h%s_prior0.json'%(density,layout,speed,h));identifier='%s_v%s_h%s'%(path.stem,speed,h)
            begin=time.perf_counter();blob=renew(template.read_bytes(),d['xyz'],origin,stamp,stamp,p,scope,c,m,None,h,ordinal+1) if template.exists() else None;source_ms=(time.perf_counter()-begin)*1000
            begin=time.perf_counter();valid=bool(blob and verify(blob,p,scope,c,m,None,stamp+.02,0));receiver_ms=(time.perf_counter()-begin)*1000
            age=float(frames[path.stem]['acquisition_ms'])/1000+(source_ms+receiver_ms)/1000+.02
            go=bool(blob and admit(blob,p,scope,c,m,None,stamp+age))
            if blob:(a.out/'packets'/(identifier+'.json')).write_bytes(blob)
            rows.append(dict(id=identifier,cloud=path.stem,reference=stamp,speed=speed,horizon=h,template_available=template.exists(),geometry=valid,action_admitted=go,source_ms=source_ms,receiver_ms=receiver_ms,acquisition_ms=frames[path.stem]['acquisition_ms'],age_s=age,packet_bytes=len(blob) if blob else 0))
    write(a.out/'renewal.csv',rows)
    roots=[]
    for row in csv.DictReader((a.reference/'probe.csv').open()):
        if row['packet_valid']!='True':continue
        blob=(a.reference/'packets'/(row['id']+'.json')).read_bytes();packet=json.loads(blob);s=packet['raw']['payload']['scope'];scope=Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);m=Motion(**packet['motion']);receiver=Receiver(p,c,scope.episode,scope.frame_id)
        roots.append(dict(id=row['id'],bootstrap=row['bootstrap'],history_accept=receiver.accept(blob,scope,m,1.02)))
    write(a.out/'history.csv',roots)
    manifest=dict(host=socket.gethostname(),trials=len(rows),geometry=sum(r['geometry'] for r in rows),action_admitted=sum(r['action_admitted'] for r in rows),near_geometry=sum(r['geometry'] and '_near_' in r['cloud'] for r in rows),history_trials=len(roots),history_accepted=sum(r['history_accept'] for r in roots),unregistered_prior_accepted=sum(r['history_accept'] and r['bootstrap']=='True' for r in roots),source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['body.py','stopping.py','renew.py','history.py','run_renewal.py','run_probe.py','test_renew.py','test_history.py']},reference_sha256=hashlib.sha256((a.reference/'probe.csv').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(Path(__file__).with_name('RENEWAL_FOLLOWUP.md').read_bytes()).hexdigest(),scope='No-prior full-body renewal from current saved scans; complete stopping budget and acquisition included; 15 hypothetical timely cold packet history audits.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
