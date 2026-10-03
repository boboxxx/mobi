#!/usr/bin/env python3
"""Dynamic family calibration and measured same-state causal trace comparisons."""
import argparse,hashlib,importlib.util,json,math,statistics,struct,sys,time,zlib
from pathlib import Path
import numpy as np
from engine import replay
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'experiments/positive_state_20261003'))
from model import centers,quantized_centers
from codec import encode,decode
spec=importlib.util.spec_from_file_location('positive_geometry',ROOT/'experiments/positive_state_20261003/evaluate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);geometry=module.geometry
HEADER=struct.Struct('<4sIIdI32s32s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack_other(kind,values,matrix,class_index,frame,stamp,contract,calibration):
    a=np.asarray(values,dtype='<f4' if kind==b'RXYZ' else '<f8')
    body=HEADER.pack(kind,class_index,frame,stamp,len(a),bytes.fromhex(contract),bytes.fromhex(calibration))
    if kind==b'RXYZ':body+=np.asarray(matrix,dtype='<f8').tobytes()
    body+=a.tobytes();return zlib.compress(body+hashlib.sha256(body).digest(),6)
def unpack_other(wire,kind,class_index,contract,calibration,anchor,road,extent):
    blob=zlib.decompress(wire);assert hashlib.sha256(blob[:-32]).digest()==blob[-32:]
    h=HEADER.unpack(blob[:HEADER.size]);assert h[0]==kind and h[1]==class_index and h[5].hex()==contract and h[6].hex()==calibration
    offset=HEADER.size
    if kind==b'RXYZ':
        matrix=np.frombuffer(blob,dtype='<f8',count=16,offset=offset).reshape(4,4);offset+=128
        assert len(blob)==offset+h[4]*12+32
        xyz=np.frombuffer(blob,dtype='<f4',count=h[4]*3,offset=offset).reshape(-1,3).astype(float)
        c,_=centers(xyz@matrix[:3,:3].T+matrix[:3,3],anchor,road,extent)
    else:
        assert len(blob)==offset+h[4]*16+32
        c=np.frombuffer(blob,dtype='<f8',count=h[4]*2,offset=offset).reshape(-1,2)
    return quantized_centers(c)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();capture=p/'capture';records=json.loads((capture/'record.json').read_bytes());episodes=json.loads((capture/'episodes.json').read_bytes());catalog=json.loads((HERE/'catalog.json').read_bytes());bps=list(catalog);rows=[];inputs={}
    for r in records:
        path=capture/r['cloud_file'];assert sha(path)==r['cloud_sha256'];inputs[str(path.relative_to(ROOT))]=sha(path)
        with np.load(path) as z:raw=z['raw'];matrix=z['transform'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)
        anchor=np.r_[r['query'],0.];yaw=math.radians(r['road_yaw']);road=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1.]])
        c,meta=centers(xyz@matrix[:3,:3].T+matrix[:3,3],anchor,road,catalog[r['blueprint']]);true=(np.asarray(r['center'])-anchor)@road
        error=float(np.min(np.linalg.norm(c-true[:2],axis=1))) if len(c) else 0.
        rows.append(dict(**r,centers=c.tolist(),centers_cm=quantized_centers(c).tolist(),available=bool(len(c)),residual_m=error,true_xy=true[:2].tolist(),anchor=anchor.tolist(),road=road.tolist()))
    score_by_ep={e['episode']['id']:max([r['residual_m'] for r in rows if r['episode_id']==e['episode']['id']]+[0.]) for e in episodes};registry={}
    for bp in bps:
        cal=[score_by_ep[e['episode']['id']] for e in episodes if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(cal)==95
        registry[bp]=dict(radius_um=math.ceil(max(cal)*1e6+1e-7)+8000,calibration_n=95,rank=95,episode_failure_target=.05,calibration_failure_bound=.95**95)
    calibration=hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest()
    basis={json.dumps(dict(anchor=r['anchor'],road=r['road']),sort_keys=True) for r in rows};assert len(basis)==1
    contract_body=dict(catalog=catalog,basis=json.loads(next(iter(basis))),model_sha256=sha(ROOT/'experiments/positive_state_20261003/model.py'),protocol_sha256=sha(HERE/'PROTOCOL.md'),scope='Independent current-frame outputs, max complete-family calibration, absolute source-aged deadlines.')
    contract=hashlib.sha256(json.dumps(contract_body,sort_keys=True).encode()).hexdigest();messages=p/'messages';messages.mkdir(exist_ok=False);out=[]
    for r in rows:
        path=capture/r['cloud_file']
        with np.load(path) as z:raw=z['raw'].copy();matrix=z['transform'].copy()
        bp=r['blueprint'];ext=catalog[bp];ci=bps.index(bp);radius=registry[bp]['radius_um'];anchor=np.asarray(r['anchor']);road=np.asarray(r['road']);methods={};reference_cm=np.array(r['centers_cm'],dtype=np.int32).reshape(-1,2)
        bounds=geometry(reference_cm,radius,ext,not r['available'])
        for method in ('union','lossless_centers','full_xyz'):
            samples=[];reference_wire=None
            for repeat in range(3):
                begin=time.perf_counter();xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)
                if method!='full_xyz':c,_=centers(xyz@matrix[:3,:3].T+matrix[:3,3],anchor,road,ext)
                if method=='union':wire=encode(quantized_centers(c),radius,r['frame'],r['timestamp'],ci,contract,calibration,not r['available'])
                else:wire=pack_other(b'RXYZ' if method=='full_xyz' else b'LCEN',xyz if method=='full_xyz' else c,matrix,ci,r['frame'],r['timestamp'],contract,calibration)
                middle=time.perf_counter()
                if method=='union':decoded=decode(wire,contract,calibration,ci,radius);cm=decoded['centers_cm'];refused=decoded['refused']
                else:cm=unpack_other(wire,b'RXYZ' if method=='full_xyz' else b'LCEN',ci,contract,calibration,anchor,road,ext);refused=not len(cm)
                got=geometry(cm,radius,ext,refused);end=time.perf_counter();assert got==bounds
                if r['available']:assert np.array_equal(cm,reference_cm)
                if reference_wire is not None:assert wire==reference_wire
                reference_wire=wire;samples.append(dict(source_s=middle-begin,receiver_s=end-middle))
            name=r['id']+'_'+method+'.bin';(messages/name).write_bytes(wire)
            methods[method]=dict(wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest(),packet='messages/'+name,samples=samples,source_us=math.ceil(max(s['source_s'] for s in samples)*1e6),receiver_us=math.ceil(max(s['receiver_s'] for s in samples)*1e6))
        methods['fixed200']=dict(methods['union']);distance=float(np.min(np.linalg.norm(reference_cm/100.-r['true_xy'],axis=1))) if r['available'] else 0.
        out.append(dict(**r,radius_um=radius,bounds=bounds,covered=not r['available'] or distance*1e6<=radius,methods=methods,source_us=math.floor(r['timestamp']*1e6),acquisition_us=math.ceil(r['acquisition_s']*1e6)))
        if len(out)%100==0:print('processed',len(out),flush=True)
    summary=[];traces=[]
    for bp in bps:
        ee=[e for e in episodes if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(ee)==60
        k=sum(any(not r['covered'] for r in out if r['episode_id']==e['episode']['id']) for e in ee)
        rr=[r for r in out if r['blueprint']==bp and r['split']=='test']
        summary.append(dict(blueprint=bp,**registry[bp],scheduled_test_episodes=60,captured_test_episodes=sum(e['status']=='captured' for e in ee),false_exclusion_episodes=k,available_frames=sum(r['available'] for r in rr),captured_frames=len(rr),scheduled_frames=360))
        for e in ee:
            frame_rows=[r for r in rr if r['episode_id']==e['episode']['id']];t0=frame_rows[0]['source_us'] if frame_rows else 0
            for bitrate in (20000000,2000000):
                for method in ('union','lossless_centers','full_xyz','fixed200'):
                    tr=replay(frame_rows,method,bitrate,t0);traces.append(dict(episode_id=e['episode']['id'],blueprint=bp,bitrate=bitrate,method=method,**tr))
    deps=[HERE/n for n in ('evaluate.py','engine.py','PROTOCOL.md','plan.json','catalog.json')]+[ROOT/'experiments/positive_state_20261003'/n for n in ('model.py','codec.py','evaluate.py')]+[ROOT/'experiments/shape_evidence_20261002/lifetime.py']
    result=dict(rows=out,episodes=episodes,registry=registry,calibration_scores=score_by_ep,contract_body=contract_body,contract_sha256=contract,calibration_sha256=calibration,summary=summary,traces=traces,source_hashes={str(f.relative_to(ROOT)):sha(f) for f in deps},input_hashes=inputs,capture_manifest_sha256=sha(capture/'manifest.json'),joint_calibration_confidence_lower=1-6*.95**95,scope='Fresh dynamic snapshot-family calibration and paid causal trace replay. No future frame gates individual outputs. Max tolerance bound assumes iid complete episodes per class. All methods recompute same union; fixed200 is a conservative TTL diagnostic. Modeled network/time domain, finite sampled motion, known class/inventory; no physical continuous driving guarantee or novelty established.')
    (p/'analysis_sheng.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
