"""Matched initialized honest-source function/deadline services; no attestation."""
import bootstrap
import hashlib,json,zlib
from fractions import Fraction as F
from fresh_io import ROOT,E,sha,canon
from fresh_inference import infer,compact,PRIMARY,threshold
KINDS=('function','deadline')
RUNTIME_SOURCES=('experiments/prospective_component_20261004/bootstrap.py', 'experiments/prospective_component_20261004/fresh_transport.py', 'experiments/prospective_component_20261004/fresh_inference.py', 'experiments/prospective_component_20261004/fresh_io.py', 'experiments/component_expiry_20261004/method.py', 'experiments/prospective_hypotheses_20261004/transport.py', 'experiments/prospective_hypotheses_20261004/inference.py', 'experiments/prospective_hypotheses_20261004/io_common.py', 'experiments/prospective_hypotheses_20261004/scores.py', 'experiments/calibrated_hypotheses_20261004/model.py', 'experiments/calibrated_hypotheses_20261004/geometry.py', 'experiments/state_predictor_20261004/predictor.py', 'experiments/state_predictor_20261004/integer_state.py', 'experiments/pose_support_20261004/observer.py', 'experiments/pose_support_20261004/directions.json', 'experiments/body_expiry_20261004/frontend.py', 'experiments/body_expiry_20261004/kernel.py', 'experiments/body_expiry_20261004/proposer.cpp')
def compress(obj):
    b=canon(obj);return zlib.compress(b+hashlib.sha256(b).digest(),6)
def expand(wire):
    b=zlib.decompress(wire);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:];return json.loads(b[:-32])
def registration(qualification,receipt_sha,measurement_freeze):
    return dict(version=1,service='Initialized same-model honest-source actor evidence, without execution attestation',catalog=qualification['catalog'],registry=qualification['registry'],calibration_receipt_sha256=receipt_sha,calibration_sha256=hashlib.sha256(canon(qualification['registry'])).hexdigest(),model_freeze_sha256=qualification['model_freeze_sha256'],measurement_freeze_sha256=qualification['measurement_freeze_sha256'],installed_sources={n:measurement_freeze['sources'][n] for n in RUNTIME_SOURCES},source_model_hashes={n:h for n,h in measurement_freeze['inputs'].items() if n.endswith('models_sheng.json')},queries_um=[[-6000000,0],[6000000,0]],query_radius_um=750000,cap_us=500000,motion=dict(speed_um_s=5000000,acceleration_um_s2=3000000))
def decode_setup(wire,contract):
    ctx=expand(wire);assert hashlib.sha256(canon(ctx)).hexdigest()==contract
    assert ctx['version']==1 and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['query_radius_um']==750000 and ctx['cap_us']==500000 and ctx['motion']==dict(speed_um_s=5000000,acceleration_um_s2=3000000)
    assert hashlib.sha256(canon(ctx['registry'])).hexdigest()==ctx['calibration_sha256']
    for n,h in ctx['installed_sources'].items():assert sha(ROOT/n)==h,n
    # Model digests identify the registered honest source; weights are source-only
    # and are checked there by freeze_check(), not unnecessarily loaded at RX.
    assert set(ctx['installed_sources'])==set(RUNTIME_SOURCES)
    for h in ctx['source_model_hashes'].values():assert len(h)==64 and len(bytes.fromhex(h))==32
    return ctx
def encode(r,family,kind,hulls,hypothesis,ctx,contract):
    obj=dict(version=1,kind=kind,family=family,blueprint=r['blueprint'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],contract=contract,calibration=ctx['calibration_sha256'])
    if kind=='function':obj.update(hulls_cm=hulls,hypothesis=hypothesis)
    else:
        assert kind=='deadline';obj.update(compact(infer(hulls,ctx['catalog'][r['blueprint']],hypothesis,threshold(ctx['registry'],r['blueprint'],family),family)))
    return compress(obj)
def decode(wire,family,kind,ctx,contract):
    obj=expand(wire);assert obj['version']==1 and obj['kind']==kind and obj['family']==family and family in PRIMARY and kind in KINDS
    assert obj['contract']==contract and obj['calibration']==ctx['calibration_sha256'] and obj['blueprint'] in ctx['catalog'] and obj['layout'] in (0,1)
    for field in ('frame','source_us'):assert type(obj[field]) is int and obj[field]>=0
    if kind=='function':out=compact(infer(obj['hulls_cm'],ctx['catalog'][obj['blueprint']],obj['hypothesis'],threshold(ctx['registry'],obj['blueprint'],family),family))
    else:
        out=dict(status=obj['status'],lower_us=obj['lower_us']);assert out['status'] in ('bounded','refused','empty');assert len(out['lower_us'])==(2 if out['status']=='bounded' else 0)
        assert all(type(v) is int and 0<=v<=500000 for v in out['lower_us'])
    return dict(**out,blueprint=obj['blueprint'],layout=obj['layout'],frame=obj['frame'],source_us=obj['source_us'])
