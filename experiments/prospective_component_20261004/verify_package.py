#!/usr/bin/env python3
"""Complete immutable source/logical-data/artifact closure, dual-host audits, explicit limits."""
import argparse,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json','calibration_frozen.json','qualification_certification_sheng.json','paid_certification_sheng.json','qualification_test_sheng.json','paid_test_sheng.json','capture/episodes.json'}
POST_REPORTS=('research/component_expiry_proof_20261004.md','research/expiry_related_work_update_20261004.md','research/expiry_control_prior_work_20261004.md','research/prospective_component_result_20261004.md','CURRENT_RESEARCH_20261004.md')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def artifacts():
    return {str(p.relative_to(ROOT)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path);a=ap.parse_args();f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    for file in ('analysis_freeze.json','analysis_supplement_freeze.json'):
        for n,h in read(E/file)['sources'].items():assert sha(ROOT/n)==h,n
    assert (P/'terminal.txt').read_text()=='FINITE_PROSPECTIVE_COMPONENT_EVALUATION_COMPLETE\n'
    assert (P/'capture_terminal.txt').read_text()=='FRESH_COMPONENT_CAPTURE_COMPLETE\n'
    assert (P/'audit_local.json').read_bytes()==(P/'audit_sheng.json').read_bytes()
    assert read(P/'server_stopped.json')['stopped'] and read(P/'capture/cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
    for descriptor in ('logical_archives.json','capture_logical_archives.json'):
        for v in read(P/descriptor)['records']:
            for field in ('logical_path','archive_path'):
                q=Path(v[field]);assert not q.is_absolute() and '..' not in q.parts and q.parts[:2]==('results',E.name)
            z=ROOT/v['archive_path'];assert sha(z)==v['archive_sha256'] and z.stat().st_size==v['archive_bytes'];h=hashlib.sha256();size=0
            with gzip.open(z,'rb') as stream:
                for b in iter(lambda:stream.read(1048576),b''):h.update(b);size+=len(b)
            assert size==v['logical_bytes'] and h.hexdigest()==v['logical_sha256']
            p=ROOT/v['logical_path']
            if p.exists():assert p.stat().st_size==size and sha(p)==h.hexdigest()
    for name in ('order_certification.json','order_test.json'):
        order=read(P/name);assert order['stage_clouds_read']==0 and order['receipt_written_before_stage_processing']
    policy=read(P/'policy_frozen.json');assert policy['certification_complete'] and policy['test_clouds_processed_before_certificate']==0
    summary=read(P/'summary_sheng.json');assert summary['policy_receipt_sha256']==sha(P/'policy_frozen.json') and summary['freeze_sha256']==sha(E/'freeze.json') and summary['policy_certified']==policy['accepted_policies'] and not summary['goal_complete']
    if a.prepare:
        sources=dict(f['sources']);inputs=dict(f['inputs'])
        for p in E.iterdir():
            if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
        for n in POST_REPORTS:sources[n]=sha(ROOT/n)
        write(P/'publication_source_manifest.json',dict(sources=sources,inputs=inputs,model_pipeline_freeze_sha256=sha(E/'freeze.json'),scope='Immutable pre-capture pipeline plus pre-outcome analysis and post-result reporting/packaging sources; no model/risk/policy retuning.'))
        files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()};assert all(v['bytes']<100*1024*1024 for v in files.values())
        write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),noncircular_and_lossless_logical_exclusions=sorted(EXCLUDE),scope='All raw clouds, actual messages, losses/fees, failures, receipts/logs, figures and lossless logical archives.'))
    pub=read(P/'publication_source_manifest.json')
    for section in ('sources','inputs'):
        for n,h in pub[section].items():assert sha(ROOT/n)==h,n
    m=read(P/'artifact_manifest.json');assert set(artifacts())==set(m['files']);assert m['file_count']==len(m['files']) and m['total_bytes']==sum(v['bytes'] for v in m['files'].values())
    for n,v in m['files'].items():
        q=Path(n);assert not q.is_absolute() and '..' not in q.parts and q.parts[:2]==('results',E.name)
        assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes'] and v['bytes']<100*1024*1024
    out=dict(artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),files=m['file_count'],bytes=m['total_bytes'],audit_sha256=sha(P/'audit_sheng.json'),calibration_receipt_sha256=summary['calibration_receipt_sha256'],policy_receipt_sha256=sha(P/'policy_frozen.json'),accepted_policies=policy['accepted_policies'],frozen_sources_valid=True,finite_independent_experiment_complete=True,live_ego_or_wireless_verified=False,goal_complete=False)
    if a.out:write(a.out,out)
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
