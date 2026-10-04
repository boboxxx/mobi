#!/usr/bin/env python3
"""Post-run same-row, same-integer-oracle comparison; no fit or risk claim."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/state_predictor_20261004'
def main():
    old=json.loads((ROOT/'results/prospective_shape_20261004/analysis_sheng.json').read_bytes());d=json.loads((P/'analysis_sheng.json').read_bytes());index={r['id']:r for r in old['rows']};comparisons=[]
    for bp in old['context']['catalog']:
        rows=[r for r in d['rows'] if r['blueprint']==bp and r['split']=='test' and r['centers_um']['ridge'] is not None];gaps=[]
        for r in rows:
            gaps.extend(max(0,o-a) for o,a in zip(r['oracle_us'],index[r['id']]['methods']['joint_hull']['lower_us']))
        vv=sorted(gaps);pos=Fraction((len(vv)-1)*95,100);j=pos.numerator//pos.denominator;p95=float(vv[j]+(vv[min(j+1,len(vv)-1)]-vv[j])*(pos-j));ridge=next(v for v in d['summary'] if v['blueprint']==bp and v['method']=='ridge');comparisons.append(dict(blueprint=bp,same_source_queries=len(gaps),joint_gap_p95_us=p95,ridge_gap_p95_us=ridge['oracle_gap_us_p95'],ridge_excluded_development_episodes=len(ridge['excluded_episodes']),planned_development_test_episodes=60))
    out=dict(comparisons=comparisons,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Same bounded source rows/exact stored oracle; reused development observations, no paid utility/fresh coverage qualification.')
    (P/'comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
