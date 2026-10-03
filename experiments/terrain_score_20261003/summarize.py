#!/usr/bin/env python3
import argparse,json,math,statistics
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();data=json.loads((a.results/'analysis_sheng.json').read_bytes());out={'known_witnesses':{s:dict(old_surviving=sum(x['old_accepted_by_stride'][s] for x in data['witnesses']),new_surviving=sum(x['accepted_by_stride'][s] for x in data['witnesses'])) for s in ('16','4','1')},'test_episodes':{bp:dict(available=s['available_test_episodes'],false_exclusions=len(s['test_false_exclusion']),refused=len(s['test_refused'])) for bp,s in data['summary'].items()},'variants':{}}
    for variant in ('inversion','inversion16000'):
        rows=json.loads((a.results/variant/'rows.json').read_bytes());ttls=[r['lower_us'] for r in rows if r['lower_us']>0];remaining=[max(0,r['lower_us']-math.ceil(r['elapsed_s']*1e6+r['index_ns']/1000+r['wire_bytes']*.4+240000)) for r in rows];out['variants'][variant]=dict(calls=len(rows),excluded_cells=sum(r['excluded_cells'] for r in rows),positive_geometric_lower=len(ttls),positive_lower_min_us=min(ttls) if ttls else None,positive_lower_max_us=max(ttls) if ttls else None,median_inversion_s=statistics.median(r['elapsed_s'] for r in rows),min_inversion_s=min(r['elapsed_s'] for r in rows),max_inversion_s=max(r['elapsed_s'] for r in rows),positive_net_usable=sum(t>0 for t in remaining),upper_witness_kind_counts={kind:sum(r['witness']['kind']==kind for r in rows) for kind in sorted({r['witness']['kind'] for r in rows})})
    out['scope']='Retrospective model/compute diagnosis, all timings measured on sheng, link costs modeled. No physical safety or near-optimality claim.';a.out.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
