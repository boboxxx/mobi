#!/usr/bin/env python3
import argparse, copy, gzip, hashlib, json, math, os, socket, sys, time
from pathlib import Path
import numpy as np
from continuity import body, LegacyReceiver, Receiver, step, wire
from native_pack import library

METHODS = ['current_full', 'nearest_fixed', 'greedy_fixed', 'greedy_bridges']
H_US = 475_000


def schedule(buffer, anchor, target):
    end, previous = anchor.endpoint_us, anchor.reference_us
    selected = []
    while previous < target['ref']:
        eligible = [x for x in buffer if previous < x['ref'] < end and x['ref'] <= target['ref']]
        if not eligible:
            return None
        x = max(eligible, key=lambda x: x['ref'])
        if x['ref'] + H_US <= end:
            return None
        selected.append(x);previous, end = x['ref'], x['ref'] + H_US
    return selected


def build(method, buffer, anchor, target, profiles, contract, diag):
    diag.clear()
    if method == 'current_full':
        raw = step(target['xyz'], target['origin'], target['stamp'], target['stamp'],
                   profiles, contract, anchor, .475, target['sequence'], full=True)
        diag.update(planned_ids=[target['id']], spans_us=[H_US], attempted_steps=1)
        return (body.canonical(dict(kind='body-evidence-v1', prior=None,
                motion=body.asdict(anchor.motion), raw=raw)) if raw else None)
    selected = schedule(buffer, anchor, target)
    if selected is None:
        diag.update(branch='no_temporal_cover', planned_ids=[], attempted_steps=0)
        return None
    spans = [H_US] * len(selected)
    if method == 'greedy_bridges':
        spans[:-1] = [selected[i + 1]['ref'] - x['ref'] + 2 for i, x in enumerate(selected[:-1])]
    diag.update(planned_ids=[x['id'] for x in selected], spans_us=spans, attempted_steps=0)
    packets = []
    for x, h in zip(selected, spans):
        raw = step(x['xyz'], x['origin'], x['stamp'], x['stamp'], profiles, contract,
                   anchor, h / body.TIME_SCALE, x['sequence'],
                   strategy='nearest' if method == 'nearest_fixed' else 'greedy')
        diag['attempted_steps'] += 1
        if raw is None:
            diag['branch'] = 'spatial_gap';return None
        packets.append(raw)
    blob = wire(anchor, packets)
    diag['branch'] = 'complete' if blob else 'bundle_cap'
    diag['steps'] = len(packets)
    diag['rays'] = sum(len(x['payload']['rays']) for x in packets)
    diag['uncapped_bytes'] = len(body.canonical(dict(kind='center-continuity-v1',
        dynamics='observation-speed-age-v1', anchor=anchor.identity, steps=packets)))
    return blob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args();a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir()
    assert all(os.environ.get(n) == '1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    start = time.perf_counter();library();load_ms=(time.perf_counter()-start)*1000
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),
                  vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
    contract=body.Contract();inputs={};rows=[];contexts=[];rng=np.random.default_rng(20261004)
    def read(p):
        b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return b
    for run in sorted(a.capture.iterdir()):
        if not (run/'record.json.gz').exists():continue
        record=json.loads(gzip.decompress(read(run/'record.json.gz')))
        if not record['initialized']:continue
        old_rx=LegacyReceiver(profiles,contract,run.name,'Carla/Maps/Town10HD_Opt')
        rx=Receiver(profiles,contract);prefix=[];anchor_blob=None;anchor=None;setup_ms=0.;failures=[]
        for d in record['decisions']:
            if d['phase']=='drive' and d['index']>=20:break
            if not d['receiver_accepted']:continue
            blob=read(run/'packets'/(d['id']+'.json'))
            plane=json.loads(blob)['raw']['payload']['scope']['plane_z']
            scope=body.Scope(run.name,old_rx.frame_id,tuple(d['query']),plane)
            motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            start=time.perf_counter();assert old_rx.accept(blob,scope,motion,d['receiver_check_time'])
            try:anchor=rx.register(old_rx,blob,scope,motion);anchor_blob=blob
            except ValueError as e:failures.append(dict(id=d['id'],error=str(e)));anchor=None
            setup_ms+=(time.perf_counter()-start)*1000
            prefix.append(d['id'])
        assert anchor is not None and anchor_blob is not None, failures
        assert anchor.identity==old_rx._last_packet
        buffer=[]
        for d in record['decisions']:
            ref=math.ceil(d['stamp']*body.TIME_SCALE)
            if ref<=anchor.reference_us:continue
            p=run/'clouds'/(d['id']+'.npz');read(p)
            with np.load(p) as c:
                x=dict(id=d['id'],ref=ref,stamp=d['stamp'],sequence=d['sequence'],
                       xyz=c['xyz'].copy(),origin=c['origin'].copy(),plane_z=float(c['plane_z']),decision=d)
            assert x['plane_z']==anchor.scope.plane_z
            buffer.append(x)
            if d['id'] not in ['drive_025','drive_039']:continue
            contexts.append(dict(run=run.name,id=d['id'],anchor=body.asdict(anchor),anchor_packet_sha256=anchor.identity,
                                 prefix_ids=prefix,prefix_revalidation_failures=failures,setup_ms=setup_ms,
                                 buffer_ids=[z['id'] for z in buffer],target=d))
            for repeat in range(3):
                order=rng.permutation(METHODS).tolist()
                for method in order:
                    diag={};start=time.perf_counter();blob=build(method,buffer,anchor,x,profiles,contract,diag)
                    gen=(time.perf_counter()-start)*1000;verification=0.;geometry=False;end=None;count=0
                    if blob:
                        start=time.perf_counter()
                        if method=='current_full':
                            probe=copy.deepcopy(old_rx);geometry=probe.accept(blob,anchor.scope,anchor.motion,d['stamp']+.02)
                            if geometry:copy.deepcopy(rx).register(probe,blob,anchor.scope,anchor.motion)
                            end=x['ref']+H_US;count=1
                        else:
                            fact=rx.inspect(blob);geometry=True;end=fact['endpoint_us'];count=fact['steps']
                        verification=(time.perf_counter()-start)*1000
                        assert geometry
                        if repeat==0:(a.out/'packets'/(run.name+'_'+d['id']+'_'+method+'.json')).write_bytes(blob)
                    wire_ms=20+(len(blob)*8/20_000 if blob else 0)
                    acquisition=d['acquisition_s']*1000
                    age_us=max(50_000,math.ceil((acquisition+gen+verification+wire_ms)/50)*50_000)
                    arrival=(x['ref']+age_us)/body.TIME_SCALE
                    timely=(copy.deepcopy(rx).accept(blob,arrival,.2) if blob and method!='current_full'
                            else bool(blob and x['ref']+age_us+200_000<end))
                    row=dict(run=run.name,id=d['id'],method=method,repeat=repeat,order=order,
                             geometry=geometry,bytes=len(blob) if blob else 0,steps=count,
                             generation_ms=gen,verification_ms=verification,acquisition_ms=acquisition,
                             wire_ms=wire_ms,age_us=age_us,endpoint_us=end,
                             usable_us=end-x['ref']-math.ceil((acquisition+gen+verification+wire_ms)*1000) if blob else None,
                             action_slack_us=end-x['ref']-age_us-200_000 if blob else None,
                             hypothetical_action_pass=bool(timely),diagnostics=diag)
                    rows.append(row);print(json.dumps(row),flush=True)
    assert len(contexts)==12 and len(rows)==144
    root=Path(__file__).resolve().parents[2];sources={}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if root in p.parents and p.is_file() and p.suffix=='.py':sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(host=socket.gethostname(),rows=rows,contexts=contexts,input_sha256=inputs,source_sha256=sources,
                library_sha256=hashlib.sha256(Path(os.environ['MOBI_COVER_LIBRARY']).read_bytes()).hexdigest(),library_load_ms=load_ms,
                protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                model_addendum_sha256=hashlib.sha256(Path(__file__).with_name('MODEL_ADDENDUM.md').read_bytes()).hexdigest(),
                scope='Targeted archived fixed-region outage backfill; all on-demand generation charged; revalidated legacy prefix setup separately measured; no counterfactual driving/WCET/physical/novelty claim.')
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
