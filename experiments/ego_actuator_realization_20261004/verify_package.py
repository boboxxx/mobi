#!/usr/bin/env python3
"""Post-result source, archive, analysis, cleanup and publication closure."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
EXCLUDE={'artifact_manifest.json','verification_local.json','verification_sheng.json'}
REPORT='research/ego_actuator_realization_result_20261004.md'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p,d):
    assert not p.exists(),p
    p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')


def hashes(mapping):
    for n,h in mapping.items():
        q=Path(n);assert not q.is_absolute() and '..' not in q.parts
        assert sha(ROOT/n)==h,n


def artifacts():
    return {str(p.relative_to(ROOT)):p for p in sorted(P.rglob('*')) if p.is_file() and str(p.relative_to(P)) not in EXCLUDE}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path);a=ap.parse_args()
    frozen=read(E/'freeze.json')
    for section in ('sources','inputs'):hashes(frozen[section])
    pre=read(P/'preregistration.json');assert pre['capture_absent_before_run'] and not pre['statistical_qualification'] and not pre['recurring_job_created'] and pre['freeze_sha256']==sha(E/'freeze.json')
    assert (P/'terminal.txt').read_text()=='FINITE_EGO_ACTUATOR_CAPTURE_AND_ANALYSIS_COMPLETE\n'
    assert read(P/'capture/cleanup.json')==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
    started,stopped=read(P/'server_start.json'),read(P/'server_stopped.json')
    for key in ('pid','executable','start_time_utc','experiment'):assert started[key]==stopped[key]
    assert stopped['stopped'] and stopped['experiment']==E.name
    assert (P/'analysis_local.json').read_bytes()==(P/'analysis_sheng.json').read_bytes()
    analysis=read(P/'analysis_sheng.json');assert analysis['planned']==analysis['captured']==36 and analysis['snapshots']==6480 and not analysis['goal_complete'] and analysis['validation']=='passed'
    assert analysis['freeze_sha256']==sha(E/'freeze.json') and analysis['outcomes_sha256']==sha(P/'capture/outcomes.json')
    outcomes=read(P/'capture/outcomes.json');plan=read(E/'plan.json');assert len(outcomes)==36 and [r['request'] for r in outcomes]==plan
    for r in outcomes:
        q=Path(r['file']);assert not q.is_absolute() and '..' not in q.parts
        p=P/'capture'/q;assert p.stat().st_size==r['archive_bytes'] and sha(p)==r['archive_sha256']
        data=gzip.decompress(p.read_bytes());assert len(data)==r['logical_bytes'] and hashlib.sha256(data).hexdigest()==r['logical_sha256']
    for name in ('tests_pre_freeze_local.log','tests_sheng.log'):
        t=(P/name).read_text();assert 'Ran 2 tests' in t and t.rstrip().endswith('OK')
    if a.prepare:
        sources=dict(frozen['sources'])
        for p in E.iterdir():
            if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
        sources[REPORT]=sha(ROOT/REPORT)
        write(P/'publication_source_manifest.json',dict(sources=sources,inputs=frozen['inputs'],scope='Pre-capture freeze plus post-result operations/report/packaging; capture/analysis unchanged.'))
        files={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in artifacts().items()}
        assert all(v['bytes']<100*1024*1024 for v in files.values())
        write(P/'artifact_manifest.json',dict(files=files,file_count=len(files),total_bytes=sum(v['bytes'] for v in files.values()),exclusions=sorted(EXCLUDE)))
    publication=read(P/'publication_source_manifest.json')
    for section in ('sources','inputs'):hashes(publication[section])
    m=read(P/'artifact_manifest.json');assert set(artifacts())==set(m['files']) and m['file_count']==len(m['files']) and m['total_bytes']==sum(v['bytes'] for v in m['files'].values())
    for n,v in m['files'].items():
        q=Path(n);assert not q.is_absolute() and '..' not in q.parts and q.parts[:2]==('results',E.name)
        assert (ROOT/n).stat().st_size==v['bytes'] and sha(ROOT/n)==v['sha256']
    out=dict(files=m['file_count'],bytes=m['total_bytes'],artifact_manifest_sha256=sha(P/'artifact_manifest.json'),publication_source_manifest_sha256=sha(P/'publication_source_manifest.json'),analysis_sha256=sha(P/'analysis_sheng.json'),planned=36,captured=36,physics_snapshots=6480,source_closure_valid=True,finite_physical_component_complete=True,scene_or_ego_policy_or_radio_qualified=False,server_stopped=True,goal_complete=False)
    if a.out:write(a.out,out)
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
