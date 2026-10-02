#!/usr/bin/env python3
import argparse, hashlib, json, time
from pathlib import Path
import stream, frontier


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();s=json.loads((a.results/'study/analysis.json').read_bytes());body=stream.body
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    rows=[]
    for ctx in s['contexts']:
        name=ctx['run'];root=a.capture/name;old=stream.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');rx=stream.Receiver(profiles,contract)
        # Original context stores complete trusted prefix; reconstruct Scope and
        # Motion directly from each packet, checked by original receiver first.
        for identity in ctx['prefix_ids']:
            blob=(root/'packets'/(identity+'.json')).read_bytes();p=json.loads(blob)
            scope=body.Scope(**p['raw']['payload']['scope']);motion=body.Motion(**p['motion'])
            ref=p['raw']['payload']['reference_us']/1e6
            assert old.accept(blob,scope,motion,ref+.02)
            anchor=rx.register(old,blob,scope,motion)
        for identity in ['drive_025','drive_039']:
            path=a.results/'study/source'/(name+'_'+identity+'.json')
            if not path.exists():
                rows.append(dict(run=name,id=identity,source_step=False));continue
            raw=json.loads(path.read_bytes());t=time.perf_counter();result=frontier.compute(rx,anchor.identity,raw)
            result['compute_ms']=(time.perf_counter()-t)*1000;h=result['horizon_us']
            assert h>=475_000 and frontier.check(rx,anchor.identity,raw,h) and not frontier.check(rx,anchor.identity,raw,h+1)
            rows.append(dict(run=name,id=identity,source_step=True,raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),result=result))
    report=dict(rows=rows,frontier_sha256=hashlib.sha256(Path(frontier.__file__).read_bytes()).hexdigest(),
                study_sha256=hashlib.sha256((a.results/'study/analysis.json').read_bytes()).hexdigest(),
                scope='Post-analysis selected-step maximum; tests H and H+1 with native full geometry; does not alter earlier timed rows or authorize an unverified historical chain.')
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))


if __name__=='__main__':main()
