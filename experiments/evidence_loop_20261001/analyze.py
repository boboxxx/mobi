#!/usr/bin/env python3
"""Replay actual decisions, raw-ray proofs and every executed control tick."""
import argparse,gzip,hashlib,json,math,socket,sys
from pathlib import Path
import numpy as np
from control import TickControl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_evidence_20261001'))
import body
from strict import Receiver
from compress import pack as compressed_pack
from renew import renew
from fast_path import Receiver as FastReceiver,renew as fast_renew


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def analyze(path,version):
    v2=version>=2
    manifest=json.loads((path/'manifest.json').read_text());root=Path(__file__).resolve().parents[2]
    for n,h in manifest['source_sha256'].items():assert sha(root/n)==h,n
    assert sha(Path(__file__).with_name('PROTOCOL.md'))==manifest['protocol_sha256']
    if v2:assert sha(Path(__file__).with_name('FAST_PATH_FOLLOWUP.md' if version==3 else 'INTEGRATION_FIX.md'))==manifest['addendum_sha256']
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();results=[]
    for f in sorted(path.glob('*/record.json.gz')):
        r=json.loads(gzip.decompress(f.read_bytes()));receiver=Receiver(profiles,contract,r['run'],'Carla/Maps/Town10HD_Opt');fast_receiver=FastReceiver(profiles,contract,r['run'],'Carla/Maps/Town10HD_Opt');template=None;event_regions={};source_matches=0
        for d in r['decisions']:
            cloud=np.load(f.parent/'clouds'/(d['id']+'.npz'));scope=body.Scope(r['run'],'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cloud['plane_z']));motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert float(cloud['timestamp'])==d['stamp'] and list(cloud['query'])==d['query']
            prior=receiver.latest_region() if r['history'] else None
            if prior and not prior.established<=d['stamp']<prior.expires:prior=None
            assert (prior.identity if prior else None)==d['prior']
            args=(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'],profiles,scope,contract,motion,prior)
            if v2:
                blob=renew(template,*args,horizon=.4,sequence=d['sequence']) if template else None
                if version==3 and template:assert fast_renew(template,*args,horizon=.4,sequence=d['sequence'])==blob
                mode='renew' if blob else 'compressed'
                if blob is None:blob=compressed_pack(*args,horizon=.4,sequence=d['sequence'])
                if blob:template=blob
                assert mode==d['source_mode']
            else:blob=body.pack(*args,horizon=.4,sequence=d['sequence'])
            assert (blob is not None)==d['geometry']
            if blob:
                assert blob==(f.parent/'packets'/(d['id']+'.json')).read_bytes()
                assert hashlib.sha256(blob).hexdigest()==d['packet_sha256']
            source_matches+=1
            accepted=bool(blob and not d['dropped'] and receiver.accept(blob,scope,motion,d['receiver_check_time'] if v2 else d['stamp']))
            assert accepted==d['receiver_accepted']
            if version==3:
                fast_accepted=bool(blob and not d['dropped'] and fast_receiver.accept(blob,scope,motion,d['receiver_check_time']))
                assert fast_accepted==accepted and fast_receiver.latest_region()==receiver.latest_region()
            region=receiver.latest_region() if accepted else None
            assert bool(region and d['now']<region.expires)==d['available']
            if version==3:assert bool(region and d['now']+.05<region.expires)==d['root_ready']
            assert d['delay_ticks']==max(1,math.ceil((d['acquisition_s']+d['generation_s']+d['verification_s']+.02)/.05))
            assert abs(d['now']-d['stamp']-d['delay_ticks']*.05)<2e-6
            if d['phase']=='drive':
                assert d['dropped']==(20<=d['index']<=24)
                event_regions[d['decision_state']['frame']]=(d,region)
        driver=TickControl(manifest['bound']);previous=None;applied=0;stale_control=0
        for state in r['ticks']:
            if previous is not None:
                assert state['frame']==previous['frame']+1 and abs(state['timestamp']-previous['timestamp']-.05)<1e-7
            event=event_regions.get(state['frame']-1)
            if event:
                d,region=event;issued=bool(d['available'] and driver.issue(region,d['decision_state'],d['decision_state']['frame'],d['now']));assert issued==d['issued']
            throttle,brake,why=driver.command(state['frame']-1)
            assert throttle==state['command_throttle'] and brake==state['command_brake'] and why==state['reason']
            assert abs(throttle-state['actual_throttle'])<1e-6 and abs(brake-state['actual_brake'])<1e-6
            if why=='COMMITTED':applied+=1
            if why=='COMMITTED' and (not driver.active or state['frame']>driver.active['command_until']):stale_control+=1
            driver.observe(state);assert driver.breach==state['breach'];previous=state
        assert driver.issued==r['issued'] and driver.breach==r['breach'] and stale_control==0
        drive=[d for d in r['decisions'] if d['phase']=='drive'];roots=[d for d in r['decisions'] if d['phase']=='root']
        results.append(dict(run=r['run'],initialized=r['initialized'],drive_decisions=len(drive),root_geometry=sum(d['geometry'] for d in roots),root_available=sum(d['available'] for d in roots),geometry=sum(d['geometry'] for d in drive),available=sum(d['available'] for d in drive),issued=r['issued'],applied_command_ticks=applied,progress_m=r['progress_m'],dropped=sum(d['dropped'] for d in drive),dropped_issued=sum(d['issued'] for d in drive if d['dropped']),breach=r['breach'],collisions=len(r['collisions']),raw_cloud_packet_replays=source_matches,verified_physics_ticks=len(r['ticks']),median_source_ms=float(np.median([d['generation_s']*1000 for d in drive])) if drive else None,median_effective_age_ms=float(np.median([(d['now']-d['stamp'])*1000 for d in drive])) if drive else None))
        print(json.dumps(results[-1]),flush=True)
    assert json.loads((path/'cleanup.json').read_text())==dict(vehicles=0,sensors=0,synchronous=False)
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--first',type=Path,required=True);ap.add_argument('--corrected',type=Path,required=True);ap.add_argument('--fast',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    report=dict(host=socket.gethostname(),first=analyze(a.first,1),corrected=analyze(a.corrected,2),fast=analyze(a.fast,3),analysis_sha256=sha(Path(__file__)),scope='Actual-ego synchronous delay co-simulation; no real-time, deployment risk, or natural-scene safety guarantee.',validation='passed')
    a.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
