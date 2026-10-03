#!/usr/bin/env python3
"""Finite paid development replay on unchanged simultaneous calibrated sets."""
import argparse,hashlib,importlib.util,json,math,sys,time,zlib
from pathlib import Path
import numpy as np
from kernel import geometry
from receiver import cache_job,replay

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
PARENT=ROOT/'experiments/prospective_expiry_20261003'
sys.path.insert(0,str(PARENT))
spec=importlib.util.spec_from_file_location('pinned_primary',PARENT/'evaluate.py')
primary=importlib.util.module_from_spec(spec);spec.loader.exec_module(primary)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def stripped(r,d,centers):
    return dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],
                centers_cm=centers.tolist(),radius_um=r['radius_um'],body_um=math.ceil(float(np.linalg.norm(d['contract_body']['catalog'][r['blueprint']]))*1e6),
                contract_sha256=d['contract_sha256'],calibration_sha256=d['calibration_sha256'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    d=read(a.parent/'analysis_sheng.json');audit=read(a.parent/'audit_sheng.json');assert audit['analysis_sha256']==sha(a.parent/'analysis_sheng.json')
    freeze=read(HERE/'freeze.json')
    for name,h in freeze['source_hashes'].items():assert sha(ROOT/name)==h,name
    for name,h in freeze['input_hashes'].items():assert sha(ROOT/name)==h,name
    bps=list(d['registry']);rows=[r for r in d['rows'] if r['split']=='test'];groups={}
    for r in rows:groups.setdefault((r['episode_id'],r['step']),[]).append(r)
    pairs={};out=[]
    for group,rr in sorted(groups.items()):
        assert len(rr)==2 and {r['layout'] for r in rr}=={0,1}
        first,second=sorted(rr,key=lambda r:r['layout']);pair_id=group[0]+'_s%02d_intersection'%group[1]
        pure={};geometry_ref=None
        for method in ('union','lossless_centers','full_xyz'):
            currents={}
            for r in rr:
                wire=(a.parent/r['methods'][method]['packet']).read_bytes();ci=bps.index(r['blueprint']);assert sha(a.parent/r['methods'][method]['packet'])==r['methods'][method]['wire_sha256']
                if method=='union':
                    dec=primary.decode(wire,d['contract_sha256'],d['calibration_sha256'],ci,r['radius_um']);cm=dec['centers_cm'];frame=dec['frame'];stamp=dec['timestamp']
                else:
                    h=primary.HEADER.unpack(zlib.decompress(wire)[:primary.HEADER.size]);frame=h[2];stamp=h[3]
                    cm=primary.unpack_other(wire,b'RXYZ' if method=='full_xyz' else b'LCEN',ci,d['contract_sha256'],d['calibration_sha256'],np.array(r['anchor']),np.array(r['road']),d['contract_body']['catalog'][r['blueprint']])
                assert frame==r['frame'] and math.floor(stamp*1e6)==r['source_us'] and cm.tolist()==r['centers_cm']
                currents[r['id']]=stripped(r,d,cm)
            for r in rr:
                current=currents[r['id']];other=currents[next(x['id'] for x in rr if x['id']!=r['id'])]
                extra={}
                for branch in ('store','combine'):
                    samples=[]
                    for repeat in range(3):
                        cache={} if branch=='store' else {(other['episode_id'],other['blueprint'],other['frame'],other['source_us']):{other['layout']:other}}
                        start=time.perf_counter();g=cache_job(cache,current);end=time.perf_counter();samples.append(end-start)
                        if branch=='store':assert g is None
                        else:
                            if geometry_ref is None:geometry_ref=g
                            assert g==geometry_ref
                    extra[branch]=dict(samples_s=samples,us=math.ceil(max(samples)*1e6))
                pure.setdefault(r['id'],{})[method]=extra
        pairs[pair_id]=dict(id=pair_id,episode_id=group[0],step=group[1],frame=first['frame'],source_us=first['source_us'],blueprint=first['blueprint'],source_ids=[first['id'],second['id']],
                            left_cm=first['centers_cm'],right_cm=second['centers_cm'],radius_um=first['radius_um'],body_um=currents[first['id']]['body_um'],geometry=geometry_ref)
        for r in rr:
            out.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],step=r['step'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],
                            available=r['available'],bounds=r['bounds'],methods=r['methods'],pair_id=pair_id,extra=pure[r['id']]))
        if len(pairs)%100==0:print('pairs',len(pairs),flush=True)
    traces=[]
    for ep in d['episodes']:
        if ep['episode']['split']!='test':continue
        rr=[r for r in out if r['episode_id']==ep['episode']['id']];t0=min((r['source_us'] for r in rr),default=0)
        for method in ('union','lossless_centers','full_xyz'):
            for bitrate in (20000000,2000000):
                traces.append(dict(episode_id=ep['episode']['id'],blueprint=ep['episode']['blueprint'],method=method,bitrate=bitrate,**replay(rr,pairs,method,bitrate,t0)))
    result=dict(pairs=pairs,rows=out,traces=traces,parent_analysis_sha256=sha(a.parent/'analysis_sheng.json'),parent_audit_sha256=sha(a.parent/'audit_sheng.json'),
                source_hashes=freeze['source_hashes'],input_hashes=freeze['input_hashes'],scope='Post-result finite receiver-set development; inherited frozen simultaneous current coverage and declared body/motion premises. No new risk fit/holdout, full-raw optimum, physical continuous safety or MobiCom novelty.')
    (a.out/'analysis_sheng.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('complete',len(pairs),len(out),len(traces),flush=True)
if __name__=='__main__':main()
