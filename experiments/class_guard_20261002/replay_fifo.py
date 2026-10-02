#!/usr/bin/env python3
"""Correct initial source/link occupancy, reusing measured services and proof outputs."""
import argparse,copy,hashlib,json,math
from pathlib import Path

def charge(ms):return math.ceil(ms*1000)
def schedule(source_arrival,generation_ms,encoding_ms,wire_bytes,rate,sender_end,link_end):
    begin=max(source_arrival,sender_end);generated=begin+charge(generation_ms);ready=generated+charge(encoding_ms);link_start=max(ready,link_end);end=link_start+math.ceil(wire_bytes*8/rate)
    return begin,generated,ready,link_start,end,end+20000
def intervals_union(intervals,start,end):
    merged=[]
    for left,right in sorted((max(a,start),min(b,end)) for a,b in intervals):
        if left>=right:continue
        if merged and left<=merged[-1][1]:merged[-1][1]=max(right,merged[-1][1])
        else:merged.append([left,right])
    return sum(b-a for a,b in merged),merged

def correct(measured):
    s=copy.deepcopy(measured);groups={};changed=0
    for x in s['rows']:groups.setdefault((x['run'],x['preset'],x['repeat'],x['method']),[]).append(x)
    for (run,preset,repeat,method),rows in groups.items():
        ctx=next(c for c in s['contexts'] if c['run']==run);rm=ctx['root_metadata'][method];rate=.5 if preset=='slow' else 20.;rootref=rm['anchor']['reference_us'];sender_end=rootref+charge(ctx['root_capture_acquisition_ms']+ctx['root_capture_generation_ms']+rm['generation_extra_ms']+rm['encoding_ms']);link_end=sender_end+math.ceil(rm['bytes']*8/rate);receipt=link_end+20000+charge(rm['validation_ms']+rm['registration_ms']);receiver_end=receipt;authority=[rm['anchor']['endpoint_us'],receipt];intervals=[(receipt,authority[0]-200000)]
        for x in rows:
            assert x['root_arrival_us']==link_end+20000 if x is rows[0] else True
            old=copy.deepcopy(x);values=schedule(x['source_arrival_us'],x['generation_ms']+x['augmentation_ms'],x['encoding_ms'],x['bytes'],rate,sender_end,link_end)
            for k,v in zip(['sender_start_us','generation_end_us','sender_end_us','link_start_us','link_end_us','receiver_arrival_us'],values):x[k]=v
            sender_end=x['sender_end_us'];link_end=x['link_end_us'];arrival=x['receiver_arrival_us'];ref=x['ref_us'];h=x['horizon_us']
            if x['dropped']:available=arrival
            else:
                x['receiver_start_us']=max(arrival,receiver_end);x['receiver_end_us']=x['receiver_start_us']+charge(x['verification_ms']);assert ref<=x['receiver_start_us'];receiver_end=x['receiver_end_us'];available=receiver_end
                if h>0 and ref+h>authority[0]:authority=[ref+h,receiver_end]
            age=max(50000,math.ceil((available-ref)/50000)*50000);tick=ref+age;x.update(total_ms=(available-ref)/1000,age_us=age,tick_us=tick,fresh_admission=bool(not x['dropped'] and h>0 and age+200000<h),current_authority=bool(tick>=receiver_end and authority[1]<=tick and tick+200000<authority[0]),authority=list(authority))
            if h>0:intervals.append((tick,ref+h-200000))
            changed+=int(x!=old)
        c=next(c for c in s['coverage'] if (c['run'],c['preset'],c['repeat'],c['method'])==(run,preset,repeat,method));covered,merged=intervals_union(intervals,c['start_us'],c['end_us']);c.update(covered_us=covered,coverage=covered/(c['end_us']-c['start_us']),intervals=merged)
    s['fifo_correction']=dict(changed_rows=changed,initial_occupancy='Sender starts after paid root assembly; serialized link starts after paid root transmission.',scope='Deterministic corrected modeled queues using unchanged recorded CPU durations, rays, dictionaries and mathematical proof outputs. No new timing measurements or real link. Every proof/source reference remains earlier than receiver start.')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();path=a.results/'study/analysis.json';s=correct(json.loads(path.read_bytes()));s['measured_study_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();s['fifo_replay_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(a.results/'fifo_corrected.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s['fifo_correction']))
if __name__=='__main__':main()
