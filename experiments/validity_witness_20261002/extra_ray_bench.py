#!/usr/bin/env python3
"""One extra real observation refutes one candidate, not a complete TTL."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
import analyze as reference
body=reference.body;ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();out=a.results/'extra_ray_study';out.mkdir(exist_ok=False);(out/'facts').mkdir();basepath=a.results/'study/analysis.json';base=json.loads(basepath.read_bytes());rows=[]
    for original in base['rows']:
        name=original['run'];identity='drive_%03d'%original['index'];capture=ROOT/'results/online_evidence_20261002/live'/name;recordpath=capture/'record.json.gz';record=json.loads(gzip.decompress(recordpath.read_bytes()));d=next(d for d in record['decisions'] if d['id']==identity);cloudpath=capture/'clouds'/(identity+'.npz')
        t=time.perf_counter()
        with np.load(cloudpath) as cloud:o,r,ref=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'])
        scope=body.Scope(**original['scope']);profiles={n:body.Profile(**p) for n,p in json.loads((ROOT/original['received_paths'][-1]).read_bytes())['payload']['profiles'].items()};contract=body.Contract();v=body.projections(o,r,ref,{original['klass']:profiles[original['klass']]},scope,contract)[original['klass']]
        witness=original['witness'];assert witness is not None;center=np.asarray(witness['center_reference'])-np.asarray(scope.query);margin=profiles[original['klass']].r_min-np.linalg.norm(v['witnesses']-center,axis=1)-v['error'];j=int(np.argmax(margin));rid=int(v['ray_indices'][j]);assert margin[j]>1e-9
        raw=json.loads(body.serialize(o,r[rid:rid+1],ref,profiles,scope,contract,.475,d['sequence']));path=out/'facts'/(name+'_'+identity+'_'+original['klass']+'.json');path.write_bytes(body.canonical(raw));ms=(time.perf_counter()-t)*1000
        selected=json.loads((ROOT/original['received_paths'][-1]).read_bytes());_,so,sr=body.decode(body.canonical(selected),profiles,scope,contract);assert (tuple(o[r[rid,0]])+tuple(r[rid,1:])) not in reference.prefix.ray_keys(so,sr)
        row=dict(run=name,index=original['index'],klass=original['klass'],ref_us=ref,witness=witness,source_path=original['received_paths'][-1],source_sha256=sha(ROOT/original['received_paths'][-1]),cloud_path=str(cloudpath.relative_to(ROOT)),cloud_sha256=sha(cloudpath),record_path=str(recordpath.relative_to(ROOT)),record_sha256=sha(recordpath),cloud_ray_index=rid,full_scan_rays=len(r),selected_rays=len(sr),fact=str(path.relative_to(out)),fact_sha256=sha(path),bytes=len(path.read_bytes()),margin_m=float(margin[j]),selection_ms=ms)
        rows.append(row);print(json.dumps({k:row[k] for k in ['run','index','klass','margin_m','bytes']}),flush=True)
    code=Path(__file__).resolve().parent;sources={str(p.relative_to(ROOT)):sha(p) for p in [code/'extra_ray_bench.py',code/'EXTRA_RAY_PROTOCOL.md']}
    (out/'analysis.json').write_text(json.dumps(dict(rows=rows,sphere_study_sha256=sha(basepath),source_sha256=sources,scope='36 one-ray sender-information diagnostics; one candidate rejected per fact, no action authority, full certificate extension, actual link or online optimality claim.'),indent=2)+'\n')
if __name__=='__main__':main()
