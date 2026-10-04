#!/usr/bin/env python3
"""Reconstruct old selected episodes; verify exact tests against SciPy references."""
import argparse,hashlib,json,math
from fractions import Fraction as F
from pathlib import Path
from scipy.stats import beta,binom
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name;OLD=ROOT/'results/prospective_hypotheses_20261004'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=read(P/'conditional_diagnostic.json');paid=read(OLD/'paid_sheng.json');q=read(OLD/'qualification_sheng.json');lookup={r['id']:r for r in q['rows']};assert d['parent_paid_sha256']==sha(OLD/'paid_sheng.json')
    seen=set();alpha=F(1,3840)
    for r in d['policies']:
        key=(r['blueprint'],r['method'],r['rate'],r['startup']);assert key not in seen;seen.add(key)
        traces=[t for t in paid['traces'] if (t['blueprint'],t['method'],t['rate'],t['startup'])==key];assert len(traces)==60
        ns=ks=0;family=r['method'].rsplit('_',1)[0]
        for tr in traces:
            grants=[v for v in tr['decisions'] if v['grant']];ns+=bool(grants)
            ks+=any(F(*lookup[v['fact_id']]['scores'][family])>F(*q['registry'][r['blueprint']][family]) for v in grants)
        assert (r['planned_episodes'],r['authorized_episodes'],r['failed_authorized_episodes'],r['family_count'])==(60,ns,ks,192)
        p=sum(F(math.comb(ns,j))*F(1,20)**j*F(19,20)**(ns-j) for j in range(ks+1)) if ns else F(1)
        assert F(*r['p_value'])==p and r['accepted']==bool(ns and p<=alpha)
        reference=1. if ns==ks else float(beta.isf(float(alpha),ks+1,ns-ks))
        assert abs(float(F(*r['conditional_upper']))-reference)<1e-12
        assert abs(float(p)-float(binom.cdf(ks,ns,.05)))<1e-12
    assert len(seen)==192 and d['zero_failure_selected_episodes_required']==161 and F(19,20)**160>alpha>=F(19,20)**161
    out=dict(policy_checks=len(seen),selected_episodes_min=min(r['authorized_episodes'] for r in d['policies']),selected_episodes_max=max(r['authorized_episodes'] for r in d['policies']),accepted=sum(r['accepted'] for r in d['policies']),failed_selected_episodes_max=max(r['failed_authorized_episodes'] for r in d['policies']),zero_failure_required=161,exact_binomial_checks=True,scipy_reference_checks=True,diagnostic_sha256=sha(P/'conditional_diagnostic.json'),source_sha256=sha(E/'check_conditional.py'),scope='Independent counts and exact rational acceptance; SciPy quantile/CDF is a numeric reference only. Old fixed policies; class-wise selected whole episodes, no new balanced certification or per-query risk.')
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print('CONDITIONAL_DIAGNOSTIC_INDEPENDENTLY_VERIFIED',flush=True)
if __name__=='__main__':main()
