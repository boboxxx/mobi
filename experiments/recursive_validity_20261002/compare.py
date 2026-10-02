"""Cross-study semantic equality and terminal/forward mask containment."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();first=json.loads((a.results/'study/analysis.json').read_bytes());second=json.loads((a.results/'dictionary_study/analysis.json').read_bytes())
    key=lambda x:tuple(x[n] for n in ['run','preset','repeat','method','index']);old={key(x):x for x in first['rows']};states=0
    for x in second['rows']:
        y=old[key(x)];assert x['horizon_us']==y['horizon_us'] and x['fact_ref_us']==y['fact_ref_us'] and x['dropped']==y['dropped']
        if x['state_key']:
            assert x['state_key']==y['state_key'];states+=1
    masks={}
    for k in first['state_files_sha256']:
        with np.load(a.results/'study/states'/(k+'.npz')) as z:masks[k]={n:z[n] for n in z.files}
    compared=0
    for x in first['rows']:
        if x['repeat']!=0 or not x['state_key'] or not x['method'].endswith('terminal'):continue
        forward=dict(x,method=x['method'].replace('terminal','forward'));y=old[key(forward)]
        for n,p in masks[x['state_key']].items():assert not np.any(p&~masks[y['state_key']][n]);compared+=1
    assert states==1368 and compared==1368
    a.out.write_text(json.dumps(dict(cross_study_horizon_and_fact_rows=len(second['rows']),equal_position_state_references=states,terminal_mask_subset_checks=compared,
                                  initial_total_bytes=sum(x['bytes'] for x in first['rows']),dictionary_total_bytes=sum(x['bytes'] for x in second['rows']),
                                  scope='Identical information and mathematical outputs across transports; terminal constraints never enlarge corresponding positional masks. Costs and timely admissions may change.'),indent=2)+'\n')
if __name__=='__main__':main()
