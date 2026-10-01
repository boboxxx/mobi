#!/usr/bin/env python3
import argparse,csv,hashlib,json,socket,time
from pathlib import Path
import numpy as np
from proof import verify,TIME_SCALE
from optimized import renew
from run_replay import profiles,setup,name
from run_study import write


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    reference=list(csv.DictReader((a.reference/'renewal.csv').open()));frames={r['id']:r for r in csv.DictReader((a.capture/'frames.csv').open())}
    p=profiles();loaded={};rows=[]
    for row in reference:
        identifier=row['id'];density,layout,scenario,step=identifier.split('_')
        if identifier not in loaded:loaded[identifier]=dict(np.load(a.capture/'clouds'/(identifier+'.npz')))
        data=loaded[identifier];box=float(row['input_box_m']);period=float(row['period_s']);mode=row['mode'];ref=float(row['reference_s'])
        scope,contract,observed=setup(data,identifier,box,period,ref)
        template_path=a.reference/'cold_packets'/(name(density+'_'+layout+'_free_00',box,period,mode)+'.json')
        source_path=a.reference/'renewed_packets'/(name(identifier,box,period,mode)+'.json')
        expected=source_path.read_bytes() if source_path.exists() else None
        # Reproduce the exact ordinal sequence in run_replay, including initialization clouds.
        ordinal=sorted(frames).index(identifier)
        begin=time.perf_counter()
        blob=renew(template_path.read_bytes(),data['xyz'],data['origin'],observed,ref,p,scope,contract,ordinal+1,mode) if template_path.exists() else None
        refresh_ms=(time.perf_counter()-begin)*1000
        if blob!=expected:raise RuntimeError('Packet differs from reference: '+name(identifier,box,period,mode))
        begin=time.perf_counter();ok=bool(blob and verify(blob,p,scope,contract,ref+.02,.05));verify_ms=(time.perf_counter()-begin)*1000
        age=float(frames[identifier]['acquisition_ms'])/1000+(refresh_ms+verify_ms)/1000+.02
        timely=bool(blob and verify(blob,p,scope,contract,ref+age,.05))
        rows.append(dict(id=identifier,input_box_m=box,period_s=period,mode=mode,byte_identical=True,
                         geometry_verified=ok,timing_budget_passed=timely,refresh_ms=refresh_ms,verify_ms=verify_ms,total_modeled_age_s=age))
    write(a.out/'fast.csv',rows)
    manifest=dict(host=socket.gethostname(),trials=len(rows),geometry=sum(r['geometry_verified'] for r in rows),timing=sum(r['timing_budget_passed'] for r in rows),
                  packet_mismatches=0,source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['optimized.py','run_fast.py','proof.py','test_optimized.py']},
                  reference_sha256=hashlib.sha256((a.reference/'renewal.csv').read_bytes()).hexdigest(),
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('FAST_FOLLOWUP.md').read_bytes()).hexdigest())
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
