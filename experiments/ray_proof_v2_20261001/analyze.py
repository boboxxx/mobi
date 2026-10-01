#!/usr/bin/env python3
import argparse,csv,hashlib,json,collections
from pathlib import Path
import numpy as np
from proof import Contract,Scope,decode,verify,TIME_SCALE
from optimized import encode_source
from run_replay import profiles,setup,name


def read(path):return list(csv.DictReader(path.open()))
def yes(row,key):return row[key]=='True'


def provenance(blob,data,observed,ref,p,scope,contract):
    payload,o,r=decode(blob,p,scope,contract)
    expected_o,expected_r,expected_ref=encode_source(data['xyz'],data['origin'],observed,ref)
    assert payload['reference_us']==expected_ref
    assert np.array_equal(o,expected_o)  # Every present acquisition uses one shared pose.
    a=np.ascontiguousarray(r).view(np.dtype((np.void,r.dtype.itemsize*5))).ravel()
    b=np.ascontiguousarray(expected_r).view(np.dtype((np.void,expected_r.dtype.itemsize*5))).ravel()
    assert np.isin(a,b).all(),'Proof ray not in current quantized source'


def analyze_dynamic(folder,manifest,p):
    packets=0
    dynamic=read(folder/'frames.csv');assert len(dynamic)==128
    assert all(r['frame']==r['sensor_frame'] and int(r['stale_frames'])==0 for r in dynamic)
    assert len(list((folder/'clouds').glob('*.npz')))==128
    checked=truncated=violations=current_violations=0;groups=collections.defaultdict(list)
    for r in dynamic:groups[r['layout']].append(r)
    for layout,rs in groups.items():
        rs.sort(key=lambda r:int(r['step']));ts=np.array([float(r['timestamp']) for r in rs])
        xy=np.array([[float(r['center_x']),float(r['center_y'])] for r in rs])
        for i,r in enumerate(rs):
            path=folder/'packets'/(r['id']+'.json')
            assert path.exists()==yes(r,'geometry_verified')
            if not path.exists():continue
            data=np.load(folder/'clouds'/(r['id']+'.npz'));stamp=float(data['timestamp'])
            scope=Scope('dynamic-v2:view'+layout,manifest['map'],tuple(data['query']),float(data['probe_z']));c=Contract()
            blob=path.read_bytes();provenance(blob,data,stamp,stamp,p,scope,c)
            assert verify(blob,p,scope,c,stamp+.02,.05)
            assert verify(blob,p,scope,c,stamp+float(r['total_modeled_age_s']),.05)==yes(r,'timing_budget_passed')
            payload=json.loads(blob)['payload'];end=(payload['reference_us']+payload['horizon_us'])/TIME_SCALE
            assert not verify(blob,p,scope,c,end+1/TIME_SCALE,0.)
            packets+=1
            current_violations+=int(np.linalg.norm(xy[i])<=3.)
            if end>ts[-1]+1e-9:truncated+=1;continue
            checked+=1;closest=np.inf
            for j in range(i,len(rs)-1):
                if ts[j]>=end:break
                fraction=min(1.,(end-ts[j])/(ts[j+1]-ts[j]));u=xy[j];v=(xy[j+1]-xy[j])*fraction
                alpha=np.clip(-np.dot(u,v)/np.dot(v,v),0,1) if np.dot(v,v)>0 else 0.
                closest=min(closest,np.linalg.norm(u+alpha*v))
            violations+=int(closest<=3.)
    assert current_violations==0 and violations==0
    cleanup=json.loads((folder/'cleanup.json').read_text())
    assert cleanup['vehicles']==cleanup['sensors']==0 and cleanup['synchronous'] is False
    speed=max(np.linalg.norm([float(r['vx']),float(r['vy']),float(r['vz'])]) for r in dynamic)
    return dict(frames=128,geometry=sum(yes(r,'geometry_verified') for r in dynamic),timing=sum(yes(r,'timing_budget_passed') for r in dynamic),max_observed_speed_mps=speed,current_center_violations=current_violations,full_horizon_checks=checked,truncated_horizons=truncated,interpolated_center_violations=violations),packets,groups


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--no-plots',action='store_true');a=ap.parse_args();root=a.results;src=Path(__file__).parent;p=profiles()
    manifests=[json.loads((root/path).read_text()) for path in ['manifest.json','fast/manifest.json','dynamic/manifest.json','local/manifest.json','dynamic_local/manifest.json']]
    for m in manifests:
        for n,h in m['source_sha256'].items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,n
    for m,protocol in zip(manifests,['PROTOCOL.md','FAST_FOLLOWUP.md','DYNAMIC_PROTOCOL.md','DYNAMIC_LOCAL_FOLLOWUP.md','DYNAMIC_LOCAL_FOLLOWUP.md']):
        assert hashlib.sha256((src/protocol).read_bytes()).hexdigest()==m['protocol_sha256']
    for n,h in manifests[0]['input_sha256'].items():assert hashlib.sha256((a.capture/'clouds'/n).read_bytes()).hexdigest()==h,n
    for n,h in manifests[0]['dependency_sha256'].items():
        folder='visibility_uncertainty_20261001' if n=='projection.py' else 'visibility_certificate_20261001'
        assert hashlib.sha256((src.parent/folder/n).read_bytes()).hexdigest()==h,n
    assert hashlib.sha256((root/'renewal.csv').read_bytes()).hexdigest()==manifests[1]['reference_sha256']
    cold=read(root/'cold.csv');warm=read(root/'renewal.csv');fast=read(root/'fast/fast.csv')
    assert len(cold)==144 and len(warm)==len(fast)==1392
    key=lambda r:(r['id'],r['input_box_m'],r['period_s'],r['mode'])
    reference={key(r):r for r in warm};assert len(reference)==1392 and {key(r) for r in fast}==set(reference)
    for r in fast:
        assert yes(r,'byte_identical') and r['geometry_verified']==reference[key(r)]['geometry_verified']
        assert yes(r,'timing_budget_passed')==(yes(r,'geometry_verified') and float(r['total_modeled_age_s'])+.05<.2+1e-6)
    local=read(root/'local/fast.csv');assert len(local)==1392 and {key(r) for r in local}==set(reference)
    assert hashlib.sha256((root/'renewal.csv').read_bytes()).hexdigest()==manifests[3]['reference_sha256']
    for r in local:
        assert yes(r,'byte_identical') and r['geometry_verified']==reference[key(r)]['geometry_verified']
        assert yes(r,'timing_budget_passed')==(yes(r,'geometry_verified') and float(r['total_modeled_age_s'])+.05<.2+1e-6)
    packets=0
    for rows,folder in [(cold,'cold_packets'),(warm,'renewed_packets')]:
        for r in rows:
            path=root/folder/(name(r['id'],float(r['input_box_m']),float(r['period_s']),r['mode'])+'.json')
            assert path.exists()==yes(r,'geometry_verified')
            if not path.exists():continue
            data=np.load(a.capture/'clouds'/(r['id']+'.npz'));ref=float(r['reference_s'])
            scope,c,obs=setup(data,r['id'],float(r['input_box_m']),float(r['period_s']),ref)
            blob=path.read_bytes();assert len(blob)==int(r['packet_bytes'])
            provenance(blob,data,obs,ref,p,scope,c)
            assert verify(blob,p,scope,c,ref+.02,.05)
            payload=json.loads(blob)['payload'];end=(payload['reference_us']+payload['horizon_us'])/TIME_SCALE
            assert not verify(blob,p,scope,c,end+1/TIME_SCALE,0.)
            packets+=1
    assert not any(yes(r,'geometry_verified') for r in cold+warm if '_near_' in r['id'])
    assert not any(yes(r,'expired_accepted') for r in warm)
    dynamic,first_packets,groups=analyze_dynamic(root/'dynamic',manifests[2],p)
    dynamic_local,local_packets,local_groups=analyze_dynamic(root/'dynamic_local',manifests[4],p)
    packets+=first_packets+local_packets
    for path in ['server_cleanup.json','server_cleanup_local.json']:
        assert json.loads((root/path).read_text())['own_server_remaining'] is False
    summary=dict(validation='passed',source_backed_packets=packets,receiver_classes=2,
        cold=dict(trials=144,geometry=sum(yes(r,'geometry_verified') for r in cold),timing=sum(yes(r,'timing_budget_passed') for r in cold)),
        renewal=dict(trials=1392,geometry=sum(yes(r,'geometry_verified') for r in warm),reference_timing=sum(yes(r,'timing_budget_passed') for r in warm),
                     optimized_timing=sum(yes(r,'timing_budget_passed') for r in fast),local_timing=sum(yes(r,'timing_budget_passed') for r in local),packet_mismatches=0),
        dynamic=dynamic,dynamic_local=dynamic_local,
        scope='Live dynamic receiver monitor, not ego control. Model-bounded geometry, checksum only, uncalibrated input boxes, modeled link/action timing.')
    (root/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not a.no_plots:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(2,2,figsize=(11,8),sharey=True)
        plot_groups=[('First implementation',k,v) for k,v in sorted(groups.items())]+[('Local lookup',k,v) for k,v in sorted(local_groups.items())]
        for ax,(stage,layout,rs) in zip(axs.ravel(),plot_groups):
            t=np.array([float(r['timestamp']) for r in rs]);t-=t[0]
            distance=[np.linalg.norm([float(r['center_x']),float(r['center_y'])]) for r in rs]
            ax.plot(t,distance,color='#79828d',label='Vehicle-center distance')
            for key,label,color in [('geometry_verified','Geometry accepted','#2a8c7a'),('timing_budget_passed','Timed acceptance','#3c6495')]:
                mask=np.array([yes(r,key) for r in rs]);ax.scatter(t[mask],np.asarray(distance)[mask],s=24,label=label,color=color)
            ax.axhline(3.,color='#b54d4d',ls='--',label='Inflated query radius')
            ax.set(title=stage+' / view '+layout,xlabel='Simulation time (s)',ylabel='Distance to query center (m)')
            ax.legend(fontsize=8)
        fig.suptitle('Moving obstacle and raw-ray proof receiver; no ego driving controller')
        fig.tight_layout();fig.savefig(root/'dynamic_monitor.png',dpi=180);fig.savefig(root/'dynamic_monitor.pdf');plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
