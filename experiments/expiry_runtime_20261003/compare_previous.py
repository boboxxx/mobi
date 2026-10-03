#!/usr/bin/env python3
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();new=ROOT/'results/expiry_runtime_20261003/native16000';old=ROOT/'results/terrain_score_20261003/inversion16000';baseline={(r['case'],r['query_index']):r for r in json.loads((old/'rows.json').read_bytes())};cases=[]
 for r in json.loads((new/'rows.json').read_bytes()):
  s=baseline[(r['case'],r['query_index'])];assert (r['lower_us'],r['upper_us'],r['excluded'])==(s['lower_us'],s['upper_us'],s['excluded_cells']);tree=json.loads(gzip.decompress((old/s['tree_file']).read_bytes()));proof=np.load(new/r['proof']);cells=np.array([n['lo']+n['hi'] for n in tree['nodes']]);np.testing.assert_array_equal(cells,proof['cells']);statuses={'pending':0,'split':1,'excluded':2,'time_retained':3,'budget_retained':4}
  expected=np.array([[-1 if n['parent'] is None else n['parent'],*n.get('children',[-1,-1]),statuses[n['status']],n['lower_us'],0] for n in tree['nodes']],dtype=np.int64);np.testing.assert_array_equal(expected,proof['meta'])
  cases.append(dict(case=r['case'],query_index=r['query_index'],nodes=len(cells),old_tree_sha256=hashlib.sha256((old/s['tree_file']).read_bytes()).hexdigest(),native_proof_sha256=hashlib.sha256((new/r['proof']).read_bytes()).hexdigest()))
 a.out.write_text(json.dumps(dict(cases=cases,matched_nodes=sum(c['nodes'] for c in cases),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Exact old/new partition, status and horizon equivalence for the observed16000-node study; no global performance or physical validity claim.'),indent=2)+'\n')
if __name__=='__main__':main()
