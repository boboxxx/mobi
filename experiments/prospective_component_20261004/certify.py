#!/usr/bin/env python3
"""Frozen-query selective certification: one IID randomly selected query per episode."""
import bootstrap
import importlib.util
from fractions import Fraction as F
from fresh_io import ROOT,E,P,read,write,sha,freeze_check
from fresh_inference import PRIMARY
from fresh_transport import KINDS
spec=importlib.util.spec_from_file_location('fixed_binomial',ROOT/'experiments/balanced_expiry_20261004/conditional.py');stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
POLICY_COUNT=6*2*2*2;TEST_COUNT=2*POLICY_COUNT

def excluded(row,family,registry):
    bp=row['blueprint']
    if family.startswith('component_'):
        mode=family[len('component_'):]
        return F(*row['scores']['supported_'+mode])>F(*registry[bp]['supported_'+mode]) or F(*row['scores']['fallback_um'])>F(*registry[bp]['fallback_um'])
    return F(*row['scores'][family])>F(*registry[bp][family])

def main():
    freeze_check();assert not (P/'policy_frozen.json').exists();assert not (P/'qualification_test_sheng.json').exists()
    d=read(P/'qualification_certification_sheng.json');paid=read(P/'paid_certification_sheng.json');plan=read(E/'plan.json');eps=[e for e in plan if e['split']=='certification'];assert len(eps)==600
    assert paid['qualification_sha256']==sha(P/'qualification_certification_sheng.json') and d['calibration_receipt_sha256']==sha(P/'calibration_frozen.json')
    rows={r['id']:r for r in d['rows']};traces={(t['episode_id'],t['method'],t['rate'],t['startup']):t for t in paid['traces']};cells=[]
    for family in PRIMARY:
        for kind in KINDS:
            method=family+'_'+kind
            for rate in (20000000,2000000):
                for startup in ('warm','cold'):
                    selected=[];exclusions=[];action_failures=[];evidence=[]
                    for e in eps:
                        tr=traces[e['id'],method,rate,startup];decision=tr['decisions'][e['selected_query_index']];assert decision['step']*2+decision['query']==e['selected_query_index'];g=bool(decision['grant']);f=a=False
                        if g:
                            fact=rows[decision['fact_id']];f=excluded(fact,family,d['registry']);a=decision['now_us']+220000-fact['source_us']>fact['oracle_us'][decision['query']]
                        selected.append(g);exclusions.append(f);action_failures.append(a);evidence.append(dict(episode_id=e['id'],query_index=e['selected_query_index'],grant=g,excluded=f,action_failed=a,fact_id=decision['fact_id']))
                    certs={name:stats.certificate(selected,fail,risk=F(1,20),delta=F(1,40),policies=TEST_COUNT) for name,fail in [('center_score',exclusions),('source_action',action_failures)]}
                    for cert in certs.values():cert['scope']='Conditional on the single independent uniform query being granted in an IID planned episode of the fixed uniform-six-class scene law and initialized measured FIFO service. Source-model/body/motion and honest execution assumptions apply; not arbitrary locations, actors or collision probability.'
                    cells.append(dict(family=family,kind=kind,rate=rate,startup=startup,accepted=all(c['accepted'] for c in certs.values()),certificates=certs,evidence=evidence))
    assert len(cells)==POLICY_COUNT
    write(P/'policy_frozen.json',dict(cells=cells,certification_complete=True,accepted_policies=sum(c['accepted'] for c in cells),policies=POLICY_COUNT,binary_tests=TEST_COUNT,risk_target=[1,20],confidence_error_budget=[1,40],zero_failure_selected_queries_required=stats.zero_failure_required(F(1,20),F(1,40),TEST_COUNT),calibration_receipt_sha256=sha(P/'calibration_frozen.json'),qualification_sha256=sha(P/'qualification_certification_sheng.json'),paid_sha256=sha(P/'paid_certification_sheng.json'),model_freeze_sha256=sha(E/'freeze.json'),test_clouds_processed_before_certificate=0,scope='Exact binomial LTT/Bonferroni on fixed independently selected per-episode queries. Certificates concern the augmented law including profiling/FIFO fees. Timings are measurements, not WCET or true wireless. Failed policy refuses deployment; no tuning/retry/replacement.'))
    print('FINITE_POLICY_CERTIFICATION_COMPLETE',sum(c['accepted'] for c in cells),'of',len(cells),flush=True)
if __name__=='__main__':main()
