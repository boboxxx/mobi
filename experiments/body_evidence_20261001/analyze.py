#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from body import *
from strict import admit,verify,Receiver
from run_probe import profiles


def read(p):return list(csv.DictReader(p.open()))
def yes(r,k):return r[k]=='True'


def setup(data,cloud,speed,acceleration):
    q=data['query'];lateral=data['origin'][:2]-q;yaw=math.atan2(-lateral[0],lateral[1])
    scope=Scope('body-probe:'+cloud,'Town10HD_Opt/world',tuple(q),float(data['probe_z']))
    return scope,Motion(acceleration=acceleration,yaw=yaw,vx=speed*math.cos(yaw),vy=speed*math.sin(yaw))


def check_packet(blob,data,stamp,p,scope,c,m,prior):
    assert verify(blob,p,scope,c,m,prior,stamp+.02,0)
    payload,o,r=decode(canonical(json.loads(blob)['raw']),p,scope,c)
    expected_o,expected_r,expected_t=encode_source(data['xyz'],data['origin'],stamp,stamp)
    assert payload['reference_us']==expected_t and np.array_equal(o,expected_o)
    a=np.ascontiguousarray(r).view(np.dtype((np.void,r.dtype.itemsize*5))).ravel()
    b=np.ascontiguousarray(expected_r).view(np.dtype((np.void,expected_r.dtype.itemsize*5))).ravel()
    assert np.isin(a,b).all()
    end=(payload['reference_us']+payload['horizon_us'])/TIME_SCALE
    assert not verify(blob,p,scope,c,m,prior,end,0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);a=ap.parse_args();src=Path(__file__).parent;p=profiles();c=Contract();root=a.results
    manifests=[]
    for folder,protocol in [('initial','PROTOCOL.md'),('corrected','BRAKING_FOLLOWUP.md'),('renewal','RENEWAL_FOLLOWUP.md')]:
        m=json.loads((root/folder/'manifest.json').read_text());manifests.append(m)
        for n,h in m['source_sha256'].items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,n
        assert hashlib.sha256((src/protocol).read_bytes()).hexdigest()==m['protocol_sha256']
        for n,h in m.get('input_sha256',{}).items():assert hashlib.sha256((a.capture/'clouds'/n).read_bytes()).hexdigest()==h,n
    assert hashlib.sha256((root/'corrected/probe.csv').read_bytes()).hexdigest()==manifests[2]['reference_sha256']
    # All reused foundations and source frames are anchored independently.
    dependencies=json.loads((root/'dependencies.json').read_text())
    for n,h in dependencies['files'].items():assert hashlib.sha256((src.parent/n).read_bytes()).hexdigest()==h,n
    for n,h in dependencies['capture'].items():assert hashlib.sha256((a.capture/n).read_bytes()).hexdigest()==h,n
    first=read(root/'initial/probe.csv');corrected=read(root/'corrected/probe.csv');warm=read(root/'renewal/renewal.csv')
    assert len(first)==len(corrected)==216 and len(warm)==1044
    initial={r['id']:r for r in first};assert len(initial)==216
    assert all(not yes(r,'packet_valid') for r in first)
    labels={r['id']:r for r in read(a.capture/'evaluation_labels.csv')}
    checked=bad_bootstrap=valid_root=0
    for row in corrected:
        assert not yes(row,'direct_coverage') or yes(initial[row['id']],'direct_coverage')
        assert yes(row,'direct_coverage')==yes(row,'packet_valid')
        path=root/'corrected/packets'/(row['id']+'.json');assert path.exists()==yes(row,'packet_valid')
        if not path.exists():continue
        data=np.load(a.capture/'clouds'/(row['cloud']+'.npz'));scope,m=setup(data,row['cloud'],float(row['speed']),8.)
        prior=Region(tuple(data['query']),m.yaw,(-2.,-1.),(2.,1.),0.,1.,1.,'explicit-initial-condition',scope.episode) if yes(row,'bootstrap') else None
        blob=path.read_bytes();check_packet(blob,data,1.,p,scope,c,m,prior);checked+=1
        assert len(blob)==int(row['packet_bytes'])
        assert admit(blob,p,scope,c,m,prior,1.+float(row['modeled_age_without_acquisition']))==yes(row,'gate_without_acquisition')
        receiver=Receiver(p,c,scope.episode,scope.frame_id);accepted=receiver.accept(blob,scope,m,1.02)
        assert accepted==(prior is None);valid_root+=int(accepted)
        label=labels[row['cloud']]
        if prior is not None and label['center_x']:
            center=np.array([[float(label['center_x']),float(label['center_y'])]])@rotation(m.yaw)
            bad_bootstrap+=int(box_distance(center,np.array([-2.,-1.]),np.array([2.,1.]))[0]<p['vehicle'].r_min)
    for row in warm:
        path=root/'renewal/packets'/(row['id']+'.json');assert path.exists()==yes(row,'geometry')
        if not path.exists():continue
        data=np.load(a.capture/'clouds'/(row['cloud']+'.npz'));_,m=setup(data,row['cloud'],float(row['speed']),8.);density,layout,scenario,_=row['cloud'].split('_');scope=Scope('body-renew:'+density+':'+layout+':'+scenario,'Town10HD_Opt/world',tuple(data['query']),float(data['probe_z']));stamp=float(row['reference'])
        blob=path.read_bytes();check_packet(blob,data,stamp,p,scope,c,m,None);checked+=1
        assert len(blob)==int(row['packet_bytes'])
        assert admit(blob,p,scope,c,m,None,stamp+float(row['age_s']))==yes(row,'action_admitted')
        assert '_near_' not in row['cloud']
    history=read(root/'renewal/history.csv');assert len(history)==15
    assert all(yes(r,'history_accept')==(r['bootstrap']=='False') for r in history)
    summary=dict(validation='passed',source_backed_geometry_packets=checked,
      initial=dict(trials=216,geometry=sum(yes(r,'direct_coverage') for r in first),packets=0,stop_contract='inconsistent; initial stop gate cannot support a claim'),
      corrected=dict(trials=216,geometry=sum(yes(r,'direct_coverage') for r in corrected),packets=sum(yes(r,'packet_valid') for r in corrected),stop_gate_without_acquisition=sum(yes(r,'gate_without_acquisition') for r in corrected),bootstrap_premise_violations=bad_bootstrap),
      receiver_history=dict(timely_root_diagnostic_accepted=valid_root,unregistered_prior_accepted=sum(yes(r,'history_accept') and r['bootstrap']=='True' for r in history)),
      renewal=dict(trials=1044,geometry=sum(yes(r,'geometry') for r in warm),complete_stop_admitted=sum(yes(r,'action_admitted') for r in warm),near_accepted=sum(yes(r,'geometry') and '_near_' in r['cloud'] for r in warm)),
      scope='Saved no-ego geometry; hypothetical velocity/body/motion/stopping contracts; no new CARLA driving. Conditional geometry positives with invalid bootstrap are explicitly not safety successes.')
    assert bad_bootstrap==3 and valid_root==6
    (root/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
