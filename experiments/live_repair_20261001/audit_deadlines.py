#!/usr/bin/env python3
import argparse,gzip,hashlib,json
from pathlib import Path
from deadline import usable,next_sample_ready


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    changed=[];roots=[];checked=0;tick_checked=0
    for f in sorted(a.capture.glob('*/record.json.gz')):
        r=json.loads(gzip.decompress(f.read_bytes()));deadlines={}
        for d in r['decisions']:
            if d['geometry']:
                blob=(f.parent/'packets'/(d['id']+'.json')).read_bytes()
                p=json.loads(blob)['raw']['payload'];expiry=p['reference_us']+p['horizon_us']
                deadlines[hashlib.sha256(blob).hexdigest()]=expiry
                strict=bool(d['receiver_accepted'] and usable(expiry,d['now']))
                if strict!=d['available']:changed.append(dict(run=r['run'],id=d['id'],old=d['available'],strict=strict,expiry_us=expiry,arrival_s=d['now']))
                if d['phase']=='root' and d['root_ready']:
                    roots.append(dict(run=r['run'],id=d['id'],old=True,strict=bool(d['receiver_accepted'] and next_sample_ready(expiry,d['now']))))
            checked+=1
        for st in r['ticks']:
            if st['renewed']:
                assert usable(deadlines[st['cached_lease']],st['before']['timestamp'],200000)
            tick_checked+=1
    result=dict(decisions_checked=checked,ticks_checked=tick_checked,availability_changes=changed,root_changes=roots,
        admitted_action_expiry_violations=0,
        qualification='No actual admissions occurred: this zero is vacuous for moving control. Corrected entry is replay/unit-tested, not freshly driven.',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('deadline.py')]})
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
