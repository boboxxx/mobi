"""Finite feasibility gate before the frozen full event study."""
import argparse,hashlib,json,time
from pathlib import Path
import context,repair
body=repair.body;G=repair.G

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False);ctx=context.load('c0_view0_reference_rate20');rows=[]
    for mode in ('scalar','fine'):
        rx=context.receiver(ctx,mode,repair.ref(ctx['root'])+1000,'backward');source=repair.Source(ctx['profiles'],ctx['contract'],rx.core.anchor);source.add(ctx['root'],ctx['capture']/'clouds'/(ctx['root_identity']+'.npz'),ctx['root_decision']['stamp']);sender=G.dictionary.Sender()
        for i in range(20,24):
            raw=ctx['original'][i];source.add(raw,ctx['capture']/'clouds'/('drive_%03d.npz'%i),ctx['decisions']['drive_%03d'%i]['stamp']);wire=sender.encode(dict(kind='position-flow-v1' if mode=='fine' else 'class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=rx.core.anchor.identity,steps=[raw]),i);start=repair.ref(raw)+100000;t=time.perf_counter();d,_=rx.normal(wire,raw,start);ms=(time.perf_counter()-t)*1000;rx.normal_finish(start+int(ms*1000)+1,d);row=dict(mode=mode,index=i,normal=d,normal_ms=ms)
            if d['horizon_us']==0:
                t=time.perf_counter();request=rx.request(raw);row['request_ms']=(time.perf_counter()-t)*1000;t=time.perf_counter();reply,stats=source.reply(request);row['source_ms']=(time.perf_counter()-t)*1000;check=rx.core.clock+100000;t=time.perf_counter();rd,_=rx.reply(reply,check);row['receiver_ms']=(time.perf_counter()-t)*1000;rx.reply_finish(check+int(row['receiver_ms']*1000)+1);row.update(repair=rd,stats=stats,request_bytes=len(request),reply_bytes=len(reply));(a.out/(mode+'_request.bin')).write_bytes(request);(a.out/(mode+'_reply.bin')).write_bytes(reply)
            rows.append(row);print(json.dumps(row),flush=True)
    (a.out/'gate.json').write_text(json.dumps(dict(rows=rows,prefix=ctx['prefix'],warm_ms=ctx['warm_ms'],scope='Feasibility only; no complete paid queues'),indent=2)+'\n')
if __name__=='__main__':main()
