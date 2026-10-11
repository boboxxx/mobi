"""Atomic simulated actuator; no hardware RPC/WCET guarantee is claimed."""
import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/closed_loop_audit_20261011'))
import fast_expiry
R=fast_expiry.R
DT=50000
ACTION=300000
MARGIN=20000
SPEED=750000
SENSING=50000
PROPAGATION=20000
RATE=20000000


def pack(obj):
    raw=R.canonical(obj)
    return zlib.compress(raw+hashlib.sha256(raw).digest(),6)


def unpack(wire):
    raw=zlib.decompress(wire)
    assert len(raw)>32 and hashlib.sha256(raw[:-32]).digest()==raw[-32:]
    return json.loads(raw[:-32])


def proposal(cache,query,context,episode,step,now,method):
    ttl=fast_expiry.expiry(cache['states'][method],query,R.A.pose.enclosing_radius_um(context['extent']),method)
    return dict(version=1,episode=episode,context=hashlib.sha256(R.canonical(context)).hexdigest(),
        seq=step,controller_sample_us=now,source_us=cache['source_us'],expiry_us=ttl,
        query_um=query,radius_um=R.RADIUS,action_us=ACTION)


def admit(lease,now,position,body_radius,episode,context_hash):
    if lease is None:
        return dict(allowed=False,reason='no_lease')
    if lease['episode']!=episode or lease['context']!=context_hash or lease['version']!=1:
        return dict(allowed=False,reason='scope_identity')
    assert lease['action_us']==ACTION and lease['radius_um']==R.RADIUS
    source,ttl=lease['source_us'],lease['expiry_us']
    assert type(source) is int and type(ttl) is int and 0<=ttl<=R.CAP
    if not 0<=source<=lease['controller_sample_us']<=now:
        return dict(allowed=False,reason='future_source_or_sample')
    if now+ACTION>source+ttl:
        return dict(allowed=False,reason='deadline')
    slack=R.RADIUS-body_radius-MARGIN-SPEED*ACTION//1000000
    distance_squared=sum((q-p)**2 for q,p in zip(lease['query_um'],position))
    if slack<0 or distance_squared>slack*slack:
        return dict(allowed=False,reason='body_scope')
    return dict(allowed=True,reason='accepted',source_us=source,expiry_us=ttl,
        deadline_us=source+ttl,action_end_us=now+ACTION,query_um=lease['query_um'],
        centre_slack_um=slack,centre_distance_squared_um2=distance_squared)


def service(arrival,free,duration):
    assert type(arrival) is int and type(free) is int and type(duration) is int and duration>=0
    return max(arrival,free)+duration


def transmit(ready,free,wire_bytes):
    end=service(ready,free,(wire_bytes*8*1000000+RATE-1)//RATE)
    return end,end+PROPAGATION
