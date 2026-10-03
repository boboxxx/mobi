#!/usr/bin/env python3
"""Hash verification for the finite published study; no simulation or retuning."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'experiments/positive_state_20261003'
P=ROOT/'results/positive_state_20261003'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    pairs=[]
    for name,script in [('audit','audit.py'),('diagnosis','diagnose.py'),('summary','summarize.py'),('expiry','check_expiry.py')]:
        a=P/(name+'_local.json');b=P/(name+'_sheng.json')
        assert a.read_bytes()==b.read_bytes(),name
        assert read(b)['source_sha256']==sha(E/script),script
        pairs.append(dict(local=a.name,sheng=b.name,sha256=sha(b)))
    analysis=read(P/'analysis_sheng.json');timing=read(P/'timing_complete_sheng.json')
    for hashes in (read(E/'capture_freeze.json')['source_hashes'],analysis['source_hashes'],analysis['input_hashes'],timing['source_hashes']):
        for name,h in hashes.items():assert sha(ROOT/name)==h,name
    assert analysis['capture_manifest_sha256']==sha(P/'capture/manifest.json')
    assert timing['analysis_sha256']==sha(P/'analysis_sheng.json')
    capture=read(P/'capture/manifest.json');records=read(P/'capture/record.json')
    assert capture['captured']==1104 and capture['rows']==len(records)==1146
    assert len(read(E/'plan.json'))==594
    for r in records:
        if r['status']=='captured':assert sha(P/'capture'/r['cloud_file'])==r['cloud_sha256'],r['id']
    assert len(analysis['rows'])==len(timing['rows'])==1104 and len(analysis['episodes'])==594
    assert len(list((P/'messages_sheng').glob('*.bin')))==1104
    for r in analysis['rows']:assert sha(P/r['packet'])==r['packet_sha256'],r['id']
    cleanup=read(P/'capture/cleanup.json');assert all(cleanup[k]==0 for k in ('vehicles','walkers','sensors')) and cleanup['synchronous'] is False
    stopped=read(P/'server_stopped.json');assert stopped['stopped'] is True and stopped['pid']==75592 and stopped['experiment']=='positive_state_20261003'
    audit=read(P/'audit_sheng.json');assert audit['packet_checks']==1104 and audit['analytic_age_checks']==6624 and audit['stored_rays']==24367488
    for name in ('audit','diagnosis','expiry'):assert read(P/(name+'_sheng.json'))['analysis_sha256']==sha(P/'analysis_sheng.json')
    diag=read(P/'diagnosis_sheng.json');assert diag['bank_sha256']==sha(ROOT/'results/nominal_witness_20261003/transfer_sheng.json')
    for r in diag['regression']:assert sha(ROOT/'results/tube_evidence_20261003/replay'/r['current_packet'])==r['current_packet_sha256']
    s=read(P/'summary_sheng.json');t=s['total']
    assert (t['test_false_exclusion_episodes'],t['scheduled_test_episodes'],t['positive_modeled_test_queries'],t['scheduled_test_queries'])==(17,360,705,1440)
    assert sum(c['positive_query_results_on_excluded_episodes'] for c in s['classes'])==40
    expiry=read(P/'expiry_sheng.json');assert expiry['summary_sha256']==sha(P/'summary_sheng.json')
    assert (expiry['positive_queries'],expiry['reachable_at_start'],expiry['reachable_by_end'])==(705,0,0)
    for host in ('local','sheng'):
        log=(P/('tests_'+host+'.txt')).read_text();assert 'Ran 10 tests' in log and log.rstrip().endswith('OK')
    if args.freeze:
        sources=set(p for p in E.iterdir() if p.is_file())|{ROOT/n for n in analysis['source_hashes']}
        sources.add(ROOT/'research/positive_state_result_20261003.md')
        # Small regression inputs not contained in the new capture/packet set.
        inputs={n:sha(ROOT/n) for n in ('results/nominal_witness_20261003/transfer_sheng.json','results/proof_repair_20261003/replay/rows.json','results/pose_inversion_20261003/replay/sources.json')}
        write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},regression_inputs=inputs,scope='Frozen study source, report and direct dependencies; rolling README/project ledger are versioned by publication commit.'))
        write(P/'verification.json',dict(deterministic_pairs=pairs,tests_per_host=10,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Fresh static known-class center calibration and conditional expiry; offline family availability, marginal coverage only. No complete physical/online safety or near-optimal full-evidence expiry established.'))
        files=sorted(p for p in P.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and '__pycache__' not in p.parts)
        write(P/'artifact_manifest.json',dict(files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},file_count=len(files),total_bytes=sum(p.stat().st_size for p in files)))
    source=read(P/'publication_source_manifest.json')
    for mapping in (source['source_files'],source['regression_inputs']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    assert read(P/'verification.json')['source_manifest_sha256']==sha(P/'publication_source_manifest.json')
    artifacts=read(P/'artifact_manifest.json')
    for name,item in artifacts['files'].items():assert sha(ROOT/name)==item['sha256'] and (ROOT/name).stat().st_size==item['bytes'],name
    print(json.dumps(dict(result_files=artifacts['file_count'],source_files=len(source['source_files']),artifact_manifest_sha256=sha(P/'artifact_manifest.json'),deterministic_pairs=len(pairs))))
if __name__=='__main__':main()
