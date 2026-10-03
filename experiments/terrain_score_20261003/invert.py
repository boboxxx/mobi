#!/usr/bin/env python3
"""Finite follow-up: twelve observed scenes, two fixed queries, one budget."""
import argparse,gzip,hashlib,importlib.util,json,sys,time
from pathlib import Path
from fractions import Fraction
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
# Explicitly load the changed point score before solver imports the historical model.
spec=importlib.util.spec_from_file_location('terrain_model',HERE/'model.py');terrain=importlib.util.module_from_spec(spec);spec.loader.exec_module(terrain)
sys.path.insert(0,str(ROOT/'experiments/pose_inversion_20261003'))
import solver
from packet import encode,decode
from cell_bounds import make_index_class
solver.score=terrain.score
TerrainIndex=make_index_class()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--analysis',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--max-nodes',default=2000,type=int);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'trees').mkdir();(a.out/'packets').mkdir()
    data=json.loads(a.analysis.read_bytes());digest=hashlib.sha256(a.analysis.read_bytes()).hexdigest();sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());bps=sorted({s['blueprint'] for s in sources});rows=[]
    for s in sources:
        with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']];wire=encode(xyz,s['source_frame'],s['source_timestamp'],z['transform'],4,bps.index(s['blueprint']),digest)
        received=decode(wire,digest,len(bps));packet_file='packets/'+s['case']+'.bin.zlib';(a.out/packet_file).write_bytes(__import__('zlib').compress(wire));t=time.perf_counter_ns();indexes=[TerrainIndex(v['points'],received['origin']) for v in received['views']];index_ns=time.perf_counter_ns()-t;q=Fraction(**data['summary'][s['blueprint']]['threshold'])
        for qi,x in enumerate((-6,6)):
            tree=solver.solve(indexes,s['extent'],np.array(s['anchor']),np.array(s['road_rotation']),(x,0),q,max_nodes=a.max_nodes,policy='priority');tree_file='trees/'+s['case']+'_q'+str(qi)+'.json.gz';content=gzip.compress(json.dumps(tree).encode(),mtime=0);(a.out/tree_file).write_bytes(content);rows.append(dict(case=s['case'],query_index=qi,stride=4,wire_bytes=len(wire),packet_file=packet_file,packet_sha256=hashlib.sha256(wire).hexdigest(),tree_file=tree_file,tree_sha256=hashlib.sha256(content).hexdigest(),lower_us=tree['lower_us'],upper_us=tree['upper_us'],excluded_cells=tree['excluded_leaves'],examined_nodes=tree['examined_nodes'],elapsed_s=tree['elapsed_s'],index_ns=index_ns,witness=tree['witness']));print(json.dumps({k:rows[-1][k] for k in ('case','query_index','lower_us','upper_us','excluded_cells','elapsed_s')}),flush=True)
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');(a.out/'manifest.json').write_text(json.dumps(dict(analysis_sha256=digest,calls=len(rows),max_nodes=a.max_nodes,stride=4,source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'invert.py',HERE/'cell_bounds.py',HERE/'model.py',ROOT/'experiments/pose_inversion_20261003/solver.py',ROOT/'experiments/pose_inversion_20261003/refined.py']},scope='Additional retrospective continuous-set computation; no new independent risk test. Same domain, clock, disc dynamics and floating-guard limits as pose inversion.'),indent=2)+'\n')
if __name__=='__main__':main()
