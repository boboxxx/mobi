#!/usr/bin/env python3
"""Independent high-precision analytic reference for finite abstract expiry."""
import argparse, hashlib, json, random
from decimal import Decimal,localcontext,ROUND_CEILING
from pathlib import Path
from lifetime import State,expiry,safe_at

def first_contact(s,q,r):
    with localcontext() as c:
        c.prec=70
        clearance=(Decimal((s.x_um-q[0])**2+(s.y_um-q[1])**2).sqrt()-s.radius_um-r)
        if clearance<=0:return Decimal(0)
        v=Decimal(s.speed_um_s);a=Decimal(s.acceleration_um_s2)
        if a:return 2*clearance/(v+(v*v+2*a*clearance).sqrt())
        if v:return clearance/v
        return Decimal('Infinity')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rng=random.Random(20261003);rows=[];checks=0
    for k in range(2000):
        q=(rng.randrange(-10000000,10000001),rng.randrange(-10000000,10000001));r=rng.randrange(0,3000001);states=[State(rng.randrange(-30000000,30000001),rng.randrange(-30000000,30000001),rng.randrange(0,4000001),rng.randrange(0,20000001),rng.randrange(0,8000001)) for _ in range(rng.randrange(1,9))];cap=10000000;result=expiry(states,q,r,cap,True);contacts=[first_contact(s,q,r) for s in states];t=min(contacts);expected=0 if t==0 else min(cap,int((t*1000000).to_integral_value(rounding=ROUND_CEILING))-1)
        assert result['safe_through_us']==expected
        if result['reason'] is None:
            assert all(safe_at(s,q,r,expected) for s in states);checks+=len(states)
            if not result['capped']:assert not safe_at(states[result['witness_index']],q,r,expected+1);checks+=1
        rows.append(dict(case=k,query_xy_um=q,query_radius_um=r,states=[s.__dict__ for s in states],result=result,reference_first_contact_s=str(t)))
    result=dict(seed=20261003,cases=len(rows),boundary_checks=checks,source_sha256=hashlib.sha256(Path(__file__).with_name('lifetime.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Analytic finite disc-model validation only; no CARLA lifetime or physical motion validation.',rows=rows);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':main()
