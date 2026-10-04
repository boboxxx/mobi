"""Initialized same-model service with shared lightweight receiver registration."""
import hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;PARENT=ROOT/'results/prospective_shape_20261004'
sys.path.insert(0,str(ROOT/'experiments/prospective_shape_20261004'))
import evaluate as parent
import lease_baseline as lease
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def registration(d):
 c=d['context'];return dict(kind='Shared lightweight registration for initialized honest-source hull/deadline services; no execution attestation.',primary_context_sha256=d['contract_sha256'],primary_sources=c['source_hashes'],catalog=c['catalog'],registry=d['registry'],calibration_sha256=d['calibration_sha256'],calibration_receipt_sha256=d['calibration_receipt_sha256'],queries_um=[[-6000000,0],[6000000,0]],query_radius_um=750000,cap_us=500000,motion=c['motion'],installed_grid_sha256=sha(ROOT/'experiments/pose_support_20261004/directions.json'),new_wire_service_sha256=sha(E/'common.py'))
def encode_setup(ctx):
 b=canon(ctx);return zlib.compress(b+hashlib.sha256(b).digest(),6)
def decode_setup(wire,expected_hash):
 b=zlib.decompress(wire);assert len(b)>32 and hashlib.sha256(b[:-32]).digest()==b[-32:] and hashlib.sha256(b[:-32]).hexdigest()==expected_hash;ctx=json.loads(b[:-32]);assert hashlib.sha256(canon(ctx['registry'])).hexdigest()==ctx['calibration_sha256'] and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['cap_us']==500000 and ctx['query_radius_um']==750000
 for n,h in ctx['primary_sources'].items():assert sha(ROOT/n)==h,n
 assert sha(ROOT/'experiments/pose_support_20261004/directions.json')==ctx['installed_grid_sha256'] and sha(E/'common.py')==ctx['new_wire_service_sha256']
 return ctx
def runtime(ctx):
 return dict(catalog=ctx['catalog'],slacks_um={bp:v['joint_slack_um'] for bp,v in ctx['registry'].items()},directions=parent.DIRECTIONS,tilt_operator_norm_upper=[87267,1000000],yaw_cell_distance_factor=[8730,1000000])
def decode(wire,method,ctx):
 if method=='hull':return parent.unpack(wire,'joint_hull',runtime(ctx),ctx['primary_context_sha256'],ctx['calibration_sha256'])
 assert method=='deadline';return lease.decode(wire,ctx['primary_context_sha256'],ctx['calibration_sha256'],ctx['catalog'])
