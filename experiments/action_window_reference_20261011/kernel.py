"""Exact finite reference; no continuous/physical safety interpretation."""
from fractions import Fraction as F
import hashlib
import json
import struct

MODELS = [(F(p,100), F(r,100), F(e,100))
          for p in (35,55,75) for r in (0,15) for e in (2,12)]
PRIOR = tuple(F(v,10) for v in (4,3,2,1,0,0,0,0,0))
HAZARD = frozenset((4,5))
HEADER = struct.Struct('!4sqIHHHHH32s')

def transition(model):
    p,r,_ = model
    rows = []
    for i in range(9):
        row = [F(0)] * 9
        if i == 8:
            row[0],row[8] = r,1-r
        else:
            row[i],row[i+1] = 1-p,p
        rows.append(tuple(row))
    return tuple(rows)

def likelihood(model, observation, state):
    if observation == 3:
        return F(2,5)
    e = model[2]
    correct = 0 if state < 2 else 1 if state < 4 else 2
    return F(3,5) * (1-e if observation == correct else e/2)

def posterior(model, observation):
    if observation not in range(4):
        raise ValueError('unknown observation')
    weights = tuple(v*likelihood(model,observation,i) for i,v in enumerate(PRIOR))
    z = sum(weights)
    if not z:
        raise ValueError('impossible observation; refuse')
    return tuple(v/z for v in weights)

def propagate(b, matrix):
    return tuple(sum(b[i]*matrix[i][j] for i in range(len(b)))
                 for j in range(len(b)))

def first_hit(b, matrix, hazard, length):
    """Risk over length+1 occupancies including the initial one."""
    surviving = tuple(F(0) if i in hazard else v for i,v in enumerate(b))
    for _ in range(length):
        surviving = propagate(surviving,matrix)
        surviving = tuple(F(0) if i in hazard else v
                          for i,v in enumerate(surviving))
    return 1-sum(surviving)

def marginal_bounds(b, matrix, hazard, length):
    values = [sum(v for i,v in enumerate(b) if i in hazard)]
    for _ in range(length):
        b = propagate(b,matrix)
        values.append(sum(v for i,v in enumerate(b) if i in hazard))
    return values[-1], min(F(1),sum(values))

def segments(allowed):
    result = []
    for age,okay in enumerate(allowed):
        if okay:
            if result and result[-1][1] == age-1:
                result[-1][1] = age
            else:
                result.append([age,age])
    return result

def context_digest(observation):
    obj = dict(action='occupy_crossing',observation=observation,
               models=[[str(x) for x in m] for m in MODELS],
               prior=[str(x) for x in PRIOR],hazard=sorted(HAZARD))
    return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).digest()

def encode(allowed, observation, length, alpha, bitmap=False):
    spans = segments(allowed)
    count = len(allowed) if bitmap else len(spans)
    header = HEADER.pack(b'AWB1' if bitmap else b'AWI1',1_000_000,50_000,
                         length,alpha.numerator,alpha.denominator,
                         len(allowed)-1,count,context_digest(observation))
    if bitmap:
        raw = bytearray((len(allowed)+7)//8)
        for i,okay in enumerate(allowed):
            if okay:
                raw[i//8] |= 1 << (i%8)
        body = header+bytes(raw)
    else:
        body = header+b''.join(struct.pack('!HH',*s) for s in spans)
    return body+hashlib.sha256(body).digest()

def decode(packet):
    if len(packet) < HEADER.size+32:
        raise ValueError('short header')
    if hashlib.sha256(packet[:-32]).digest() != packet[-32:]:
        raise ValueError('packet checksum mismatch')
    packet = packet[:-32]
    magic,source,tick,length,num,den,maximum,count,digest = HEADER.unpack_from(packet)
    if magic not in (b'AWI1',b'AWB1') or source < 0 or tick == 0 or length == 0 or den == 0 or num > den:
        raise ValueError('invalid contract')
    allowed = [False]*(maximum+1)
    raw = packet[HEADER.size:]
    if magic == b'AWB1':
        if count != maximum+1 or len(raw) != (count+7)//8:
            raise ValueError('invalid bitmap length')
        if count%8 and raw[-1] >> (count%8):
            raise ValueError('noncanonical padding')
        allowed = [bool(raw[i//8] & (1 << (i%8))) for i in range(count)]
    else:
        if len(raw) != 4*count or count > maximum+1:
            raise ValueError('invalid interval length')
        last = -2
        for i in range(count):
            lo,hi = struct.unpack_from('!HH',raw,4*i)
            if lo > hi or hi > maximum or lo <= last+1:
                raise ValueError('noncanonical interval')
            allowed[lo:hi+1] = [True]*(hi-lo+1)
            last = hi
    return dict(source=source,tick=tick,length=length,alpha=F(num,den),
                digest=digest,allowed=allowed)

def admissible(packet, expected_digest, expected_length, expected_alpha,
               observation_now_us, fee_us):
    d = decode(packet)
    if (d['digest'] != expected_digest or d['length'] != expected_length or
            d['alpha'] != expected_alpha or fee_us < 0):
        return False
    age_us = observation_now_us+fee_us-d['source']
    # This exact discrete diagnostic cannot authorize off-grid interpolation.
    if age_us < 0 or age_us % d['tick']:
        return False
    age = age_us//d['tick']
    return age < len(d['allowed']) and d['allowed'][age]
