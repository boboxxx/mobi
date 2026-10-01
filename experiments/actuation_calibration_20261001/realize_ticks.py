#!/usr/bin/env python3
"""Post-analysis, monotone enlargement to the simulator's 50 ms stop grid.

No refitting, recalibration or new independent test is performed. Keep the raw
seven failures. Rounding can only enlarge the time envelope; it does not fix
unobserved inter-sample behavior or deployment distribution shift.
"""
import argparse,csv,json,math
from fractions import Fraction
from pathlib import Path
import numpy as np


def outward_ticks(seconds,dt=.05):
    if not math.isfinite(seconds) or seconds<0:return None
    return math.ceil(Fraction.from_float(float(seconds))/Fraction.from_float(float(dt)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();rows=list(csv.DictReader((a.results/'analysis/test_predictions.csv').open()));out=[]
    for r in rows:
        raw=float(r['predicted_stop_s']) if r['predicted_stop_s'] else math.inf;n=outward_ticks(raw);observed=round(float(r['observed_stop_s'])/.05) if r['observed_stop_s'] else None
        space_failure=any(not r['observed_'+k] or not r['predicted_'+k] or float(r['observed_'+k])>float(r['predicted_'+k])+1e-12 for k in ['front_m','rear_m','lateral_m'])
        exceeded=space_failure or observed is None or (n is not None and observed>n)
        # Same fixed 400 ms region and 130 ms counterfactual age as the protocol.
        admitted=n is not None and r['space']=='True' and 130000+n*50000<400000
        out.append(dict(id=r['id'],kind=r['kind'],raw_stop_s=raw if math.isfinite(raw) else None,realized_ticks=n,realized_stop_s=n*.05 if n is not None else None,joint_exceedance=exceeded,counterfactual_admit=admitted,physical_movement_authorized=False))
    with (a.results/'tick_realization.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    report=dict(scope='Post-analysis deterministic enlargement using the already prescribed 50 ms grid; same test data, not a new independent validation. No refitting or changed calibration correction.',methods={})
    for kind in ['constant','state']:
        s=[r for r in out if r['kind']==kind];times=[r['realized_stop_s'] for r in s if r['realized_stop_s'] is not None];report['methods'][kind]=dict(n=len(s),joint_exceedances=sum(r['joint_exceedance'] for r in s),counterfactual_admissions=sum(r['counterfactual_admit'] for r in s),median_stop_s=float(np.median(times)) if times else None,mean_stop_s=float(np.mean(times)) if times else None,tick_counts={str(t):sum(r['realized_ticks']==t for r in s) for t in sorted({r['realized_ticks'] for r in s if r['realized_ticks'] is not None})})
    (a.results/'tick_realization.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
