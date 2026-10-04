#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');a=ap.parse_args();d=read(P/'analysis_sheng.json');pairs=[]
    for stem,source in [('audit','audit.py'),('summary','summarize.py'),('merge_diagnosis','diagnose_merges.py'),('body_support','body_support.py'),('body_support_audit','body_support_audit.py')]:
        assert (P/(stem+'_local.json')).read_bytes()==(P/(stem+'_sheng.json')).read_bytes(),stem
        out=read(P/(stem+'_sheng.json'));assert out['source_sha256']==sha(E/source)
        if 'analysis_sha256' in out:assert out['analysis_sha256']==sha(P/'analysis_sheng.json')
        pairs.append(dict(stem=stem,sha256=sha(P/(stem+'_sheng.json'))))
    for mapping in (d['source_hashes'],d['input_hashes'],read(E/'freeze.json')['sources']):
        for n,h in mapping.items():assert sha(ROOT/n)==h,n
    for study,h in read(E/'freeze.json')['parents'].items():assert sha(ROOT/'results'/study/'analysis_sheng.json')==h
    assert len(d['rows'])==5304 and sum(len(r['variants']) for r in d['rows'])==15912 and (P/'run_terminal.txt').read_text()=='complete\n'
    assert read(P/'summary_sheng.json')['audit_sha256']==sha(P/'audit_sheng.json')
    audit=read(P/'body_support_audit_sheng.json');body=read(P/'body_support_sheng.json');assert audit['body_sha256']==sha(P/'body_support_sheng.json') and audit['frames']==5304 and audit['group_checks']==7389 and audit['quantized_point_checks']==945120
    assert all(r['development_slack_um']==0 and r['fitted_support_excluded_episodes']==0 for r in body['summary'])
    assert next(c for c in read(P/'summary_sheng.json')['classes'] if c['blueprint']=='vehicle.mercedes.sprinter')['variants'][0]['excluded_episodes']==10
    for host in ['local','sheng']:
        for stem,n in [('tests',3),('tests_support',2)]:
            log=(P/(stem+'_'+host+'.txt')).read_text();assert 'Ran '+str(n)+' tests' in log and log.rstrip().endswith('OK')
        assert read(P/('merge_diagnosis_'+host+'_at_first_run.json'))['source_sha256']==sha(E/'diagnose_merges_at_first_run.py')
    assert read(P/'body_support_local_at_first_run.json')['source_sha256']==sha(E/'body_support_at_first_run.py')
    assert (E/'diagnose_merges_at_first_run.py').read_text().replace('span_m=(hi-lo).tolist(),observed_box_midpoint=((lo+hi)/2).tolist()','span_m=[round(float(x),9) for x in hi-lo],observed_box_midpoint=[round(float(x),9) for x in (lo+hi)/2]')==(E/'diagnose_merges.py').read_text()
    difference=read(P/'merge_first_run_difference.json');assert difference['all_nonfloating_fields_equal'] and difference['maximum_absolute_difference']<=1e-10
    if a.freeze:
        files={p for p in E.iterdir() if p.is_file()}|{ROOT/'research/background_frontend_result_20261004.md'}|{ROOT/n for n in d['source_hashes']}
        write(P/'publication_source_manifest.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_files={str(f.relative_to(ROOT)):sha(f) for f in sorted(files)}))
        write(P/'verification.json',dict(deterministic_pairs=pairs,frontend_tests_per_host=3,support_tests_per_host=2,source_manifest_sha256=sha(P/'publication_source_manifest.json'),goal_complete=False,scope='Completed finite frontend and body-support diagnostics; no computed body-support expiry/tightness/paid utility, new prospective risk or physical/live/novelty completion.'))
        result_files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json')
        write(P/'artifact_manifest.json',dict(files={str(f.relative_to(ROOT)):dict(sha256=sha(f),bytes=f.stat().st_size) for f in result_files},file_count=len(result_files),total_bytes=sum(f.stat().st_size for f in result_files)))
    for n,h in read(P/'publication_source_manifest.json')['source_files'].items():assert sha(ROOT/n)==h,n
    manifest=read(P/'artifact_manifest.json');assert {str(p.relative_to(ROOT)) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'}==set(manifest['files'])
    for n,m in manifest['files'].items():assert sha(ROOT/n)==m['sha256'] and (ROOT/n).stat().st_size==m['bytes'],n
    print(json.dumps(dict(result_files=manifest['file_count'],deterministic_pairs=len(pairs),artifact_manifest_sha256=sha(P/'artifact_manifest.json'))))
if __name__=='__main__':main()
