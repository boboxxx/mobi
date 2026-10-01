#!/usr/bin/env python3
import argparse,csv,hashlib,json,socket,time
from pathlib import Path
import numpy as np
from incremental import pp,Verifier
from binary_proof import encode,BinaryVerifier
from strict_policy import verify


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--template',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    obj=json.loads(a.template.read_bytes());s=obj['raw']['payload']['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
    profiles={k:pp.Profile(**v) for k,v in obj['raw']['payload']['profiles'].items()};contract=pp.Contract();policy=pp.Policy();speed=obj['speed'];yaw=obj['yaw']
    p,o,r=pp.decode(pp.canonical(obj['raw']),profiles,scope,contract);iv=Verifier();bf=BinaryVerifier(False);bi=BinaryVerifier(True);rows=[]
    for shift in [0,1,5,20,100]:
     for age in [0,10000,50000,100000]:
      for fraction in [1.,.9,.5]:
       for reverse in [False,True]:
        q=r[:max(1,int(len(r)*fraction))].copy();q[:,1]+=shift;q[:,4]-=age
        if reverse:q=q[::-1].copy()
        raw=json.loads(pp.serialize(o,q,p['reference_us'],profiles,scope,contract,.4,0));blob=pp.canonical(dict(kind='policy-evidence-v1',policy=pp.asdict(policy),speed=speed,yaw=yaw,raw=raw));binary=encode(o,q,p['reference_us'],profiles,scope,contract,policy,speed,yaw,.4,0)
        args=(profiles,scope,contract,policy,speed,yaw,1.02);calls={'reference':lambda:verify(blob,*args),'hints':lambda:iv.verify(blob,*args),'binary_full':lambda:bf.verify(binary,*args),'binary_hints':lambda:bi.verify(binary,*args)}
        order=list(calls);offset=len(rows)%4;order=order[offset:]+order[:offset];row=dict(shift_mm=shift,age_us=age,retained=fraction,reversed=reverse)
        for name in order:
            begin=time.perf_counter();row[name]=calls[name]();row[name+'_ms']=(time.perf_counter()-begin)*1000
        row['all_equal']=len({row[name] for name in calls})==1;rows.append(row)
    keys=['shift_mm','age_us','retained','reversed']+[item for name in ['reference','hints','binary_full','binary_hints'] for item in [name,name+'_ms']]+['all_equal']
    with (a.out/'perturbation.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)
    src=Path(__file__).parent;manifest=dict(host=socket.gethostname(),cases=len(rows),equal=sum(r['all_equal'] for r in rows),positive=sum(r['reference'] for r in rows),source_sha256={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in ['run_perturbation.py','incremental.py','binary_proof.py']},protocol_sha256=hashlib.sha256((src/'PERTURBATION_PROTOCOL.md').read_bytes()).hexdigest(),template_sha256=hashlib.sha256(a.template.read_bytes()).hexdigest(),scope='Synthetic integer-ray perturbations; no new sensor capture or physical safety calibration.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
