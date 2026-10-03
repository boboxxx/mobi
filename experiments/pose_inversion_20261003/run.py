#!/usr/bin/env python3
"""Finite saved-source replay; receiver never receives actor ground truth."""
import argparse,gzip,hashlib,json,math,socket,time,zlib
from fractions import Fraction
from pathlib import Path
import numpy as np
from bounds import RayIndex,rotation
from packet import encode,decode
from solver import solve
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir();(a.out/'trees').mkdir();catalog=json.loads((HERE/'catalog.json').read_bytes());blueprints=sorted(catalog);records=[];sources=[]
    for blueprint in blueprints:
        base=ROOT/'results/shape_evidence_20261002'
        if blueprint.startswith('walker.'):base=base/'availability_followup'
        analysis_path=base/'analysis_sheng.json';analysis=json.loads(analysis_path.read_bytes());cal_digest=sha(analysis_path);q=analysis['summary'][blueprint]['joint']['threshold'];threshold=Fraction(q['numerator'],q['denominator']);capture=base/'capture';rr=json.loads((capture/'record.json').read_bytes());extent=np.asarray(catalog[blueprint]['extent']);assert catalog[blueprint]['box_rotation']==[0.,0.,0.]
        for episode_index in (0,10):
            selected=[r for r in rr if r['status']=='captured' and r['blueprint']==blueprint and r['episode']['split']=='test' and r['episode']['index']==episode_index and r['layout']==0];case=blueprint.replace('.','_')+'_test%02d'%episode_index
            if not selected:sources.append(dict(case=case,status='unavailable',blueprint=blueprint,episode_index=episode_index));continue
            assert len(selected)==1;r=selected[0];file=capture/r['cloud_file'];assert sha(file)==r['cloud_sha256']
            with np.load(file) as z:raw=z['raw'];matrix=z['transform'];stamp=float(z['timestamp'])
            anchor=np.array([*r['query'],r['plane_z']-.6]);road=rotation(0,math.radians(r['road_yaw']),0)
            source=dict(case=case,status='available',blueprint=blueprint,episode_index=episode_index,source_id=r['id'],source_cloud=str(file.relative_to(ROOT)),source_cloud_sha256=sha(file),source_record=str((capture/'record.json').relative_to(ROOT)),source_record_sha256=sha(capture/'record.json'),calibration_analysis=str(analysis_path.relative_to(ROOT)),calibration_sha256=cal_digest,anchor=anchor.tolist(),road_rotation=road.tolist(),extent=extent.tolist(),threshold=q,source_frame=r['frame'],source_timestamp=stamp);sources.append(source)
            for stride in (16,4,1):
                t=time.perf_counter_ns();xyz=np.c_[raw['x'],raw['y'],raw['z']];payload=encode(xyz,r['frame'],stamp,matrix,stride,blueprints.index(blueprint),cal_digest);encoder_ns=time.perf_counter_ns()-t;packetfile=a.out/'packets'/(case+'_s%d.bin.zlib'%stride);packetfile.write_bytes(zlib.compress(payload));packet_digest=hashlib.sha256(payload).hexdigest()
                for query_index,query in enumerate([(-6.,0.),(6.,0.)]):
                    for policy in ('priority','fifo'):
                        key=case+'_q%d_s%d_%s'%(query_index,stride,policy);begin=time.perf_counter_ns();decoded=decode(payload,cal_digest,len(blueprints));indexes=[RayIndex(v['points'],decoded['origin']) for v in decoded['views']];initialized=time.perf_counter_ns();result=solve(indexes,extent,anchor,road,query,threshold,2000,policy);finished=time.perf_counter_ns();tree=a.out/'trees'/(key+'.json.gz')
                        with gzip.GzipFile(filename=str(tree),mode='wb',mtime=0) as f:f.write((json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode())
                        receiver_ns=finished-begin;virtual_age_us=math.ceil((encoder_ns+receiver_ns)/1000+.02*1e6+len(payload)*8/20000000*1e6);usable=max(0,result['lower_us']-virtual_age_us-20000-200000)
                        row=dict(id=key,case=case,blueprint=blueprint,query_index=query_index,stride=stride,policy=policy,lower_us=result['lower_us'],upper_us=result['upper_us'],gap_us=result['gap_us'],examined_nodes=result['examined_nodes'],excluded_leaves=result['excluded_leaves'],retained_leaves=result['retained_leaves'],witness=result['witness'],packet_file=str(packetfile.relative_to(a.out)),packet_sha256=packet_digest,wire_bytes=len(payload),encoder_ns=encoder_ns,decode_index_ns=initialized-begin,receiver_ns=receiver_ns,solver_s=result['elapsed_s'],modeled_age_us=virtual_age_us,usable_lower_us=usable,source_timestamp=stamp,virtual_ready_timestamp=stamp+virtual_age_us/1e6,tree_file=str(tree.relative_to(a.out)),tree_sha256=sha(tree));records.append(row);(a.out/'rows.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({k:row[k] for k in ['id','lower_us','upper_us','examined_nodes','excluded_leaves','usable_lower_us']}),flush=True)
    (a.out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n');(a.out/'manifest.json').write_text(json.dumps(dict(host=socket.gethostname(),source_cases=len(sources),calls=len(records),protocol_sha256=sha(HERE/'PROTOCOL.md'),source_manifest_sha256=sha(HERE/'source_manifest.json'),scope='Retrospective finite replay with explicit upright flat-road priors; modeled links; geometry-only receiver inputs; no fresh capture, real driving or physical certificate.'),indent=2)+'\n')
if __name__=='__main__':main()
