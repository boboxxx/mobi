#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,socket,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evidence_loop_20261001'))
from control import TickControl
from fast_path import body,Receiver,renew as original_renew
from repair_renew import renew as repair_renew
from strict import Receiver as ReferenceReceiver
from compress import pack


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();root=Path(__file__).resolve().parents[2];manifest=json.loads((a.capture/'manifest.json').read_text())
    for n,h in manifest['source_sha256'].items():assert sha(root/n)==h,n
    assert sha(Path(__file__).with_name('PROTOCOL.md'))==manifest['protocol_sha256']
    assert sha(Path(__file__).with_name('LIFECYCLE_FIX.md'))==manifest['lifecycle_addendum_sha256']
    p=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();summaries=[]
    for f in sorted(a.capture.glob('*/record.json.gz')):
        r=json.loads(gzip.decompress(f.read_bytes()));rx=Receiver(p,c,r['run'],'Carla/Maps/Town10HD_Opt');reference=ReferenceReceiver(p,c,r['run'],'Carla/Maps/Town10HD_Opt');template=None;arrivals=[];verified=0;blob_bytes=0
        for d in r['decisions']:
            cl=np.load(f.parent/'clouds'/(d['id']+'.npz'));scope=body.Scope(r['run'],'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert float(cl['timestamp'])==d['stamp'] and list(cl['query'])==d['query']
            prior=rx.latest_region()
            if prior and not (prior.established<=d['stamp'] and math.ceil(d['stamp']*body.TIME_SCALE)<rx._deadlines[prior.identity]):prior=None
            assert (prior.identity if prior else None)==d['prior']
            args=(cl['xyz'],cl['origin'],d['stamp'],d['stamp'],p,scope,c,m,prior);renew=original_renew if r['method']=='original' else repair_renew
            blob=renew(template,*args,.4,d['sequence']) if template else None;mode=r['method'] if blob else 'compressed'
            if blob is None:blob=pack(*args,.4,d['sequence'])
            if blob:
                assert blob==(f.parent/'packets'/(d['id']+'.json')).read_bytes() and hashlib.sha256(blob).hexdigest()==d['packet_sha256'];template=blob;blob_bytes+=len(blob)
            assert mode==d['source_mode'] and bool(blob)==d['geometry'];verified+=1
            accepted=bool(blob and not d['dropped'] and rx.accept(blob,scope,m,d['receiver_check_time']));other=bool(blob and not d['dropped'] and reference.accept(blob,scope,m,d['receiver_check_time']))
            assert accepted==other==d['receiver_accepted'] and rx.latest_region()==reference.latest_region()
            region=rx.latest_region() if accepted else None
            assert bool(region and d['now']<region.expires)==d['available']
            assert bool(region and d['now']+.05<region.expires)==d['root_ready']
            if d['available']:arrivals.append((d['now'],region))
            assert d['issued'] is False
            assert d['delay_ticks']==max(1,math.ceil((d['acquisition_s']+d['generation_s']+d['verification_s']+.02)/.05))
            assert abs(d['now']-d['stamp']-.05*d['delay_ticks'])<2e-6
            if d['phase']=='drive':assert d['dropped']==(20<=d['index']<=24)
        driver=TickControl(manifest['bound']);previous=None;cached=None;available_at=None;event_index=0;applied=0
        for st in r['ticks']:
            before=st['before']
            if before is None:
                assert previous is None and st['registration_tick'] and not st['driving'] and not st['renewed'] and st['reason']=='FULL_BRAKE' and st['actual_throttle']==0 and st['actual_brake']==1
                previous=st;continue
            assert not st['registration_tick'] and st['frame']==before['frame']+1
            if previous:
                assert before['frame']==previous['frame'] and before['timestamp']==previous['timestamp']
                for k in ['x','y','z','speed','yaw','pitch','roll']:assert before[k]==previous[k]
            while event_index<len(arrivals) and arrivals[event_index][0]<=before['timestamp']:
                available_at,cached=arrivals[event_index];event_index+=1
            assert (cached.identity if cached else None)==st['cached_lease'] and available_at==st['cached_available_at']
            renewed=bool(st['driving'] and cached and driver.issue(cached,before,before['frame'],before['timestamp']));assert renewed==st['renewed']
            throttle,brake,why=driver.command(before['frame']);assert throttle==st['command_throttle'] and brake==st['command_brake'] and why==st['reason'];assert abs(throttle-st['actual_throttle'])<1e-6 and abs(brake-st['actual_brake'])<1e-6
            applied+=why=='COMMITTED';driver.observe(st);assert driver.breach==st['breach'];previous=st
        assert driver.issued==r['issued'] and driver.breach==r['breach']
        drive=[d for d in r['decisions'] if d['phase']=='drive'];drops=[d for d in drive if d['dropped']];drop_stats=None
        if drops:
            start=next(st for st in r['ticks'] if st['frame']==drops[0]['frame']);period=[st for st in r['ticks'] if drops[0]['stamp']<=st['timestamp']<=drops[-1]['now']]
            drop_stats=dict(valid_messages_suppressed=sum(d['geometry'] for d in drops),speed_at_first_drop_start=start['before']['speed'],committed_ticks=sum(st['reason']=='COMMITTED' for st in period),full_brake_ticks=sum(st['reason']=='FULL_BRAKE' for st in period),end_speed=period[-1]['speed'] if period else None)
        row=dict(run=r['run'],method=r['method'],repeat=r['repeat'],layout=r['layout'],initialized=r['initialized'],input_frames=verified,physics_ticks=len(r['ticks']),driving_decisions=len(drive),drive_geometry=sum(d['geometry'] for d in drive),drive_available=sum(d['available'] for d in drive),issued=driver.issued,applied_committed_ticks=applied,progress_m=r['progress_m'],peak_speed=max((st['speed'] for st in r['ticks']),default=0.),breach=r['breach'],collisions=len(r['collisions']),packet_bytes=blob_bytes,drop=drop_stats,median_drive_age_ms=float(np.median([(d['now']-d['stamp'])*1000 for d in drive])) if drive else None,median_gate_ms=float(np.median([st['gate_s']*1000 for st in r['ticks']])) if r['ticks'] else None)
        summaries.append(row);print(json.dumps(row),flush=True)
    assert len(summaries)==8 and json.loads((a.capture/'cleanup.json').read_text())==dict(vehicles=0,sensors=0,synchronous=False)
    report=dict(host=socket.gethostname(),runs=summaries,validation='passed',analysis_sha256=sha(Path(__file__)),source_regeneration=True,reference_receiver_equivalence=True,control_and_delayed_cache_replay=True,scope='Finite fresh synchronous delay co-simulation; no real-time, deployment risk or physical safety guarantee.')
    a.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
