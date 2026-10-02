#!/usr/bin/env python3
import hashlib,json,shutil,socket,tarfile
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[2];out=root/'results/online_evidence_20261002';deps={}
    live=json.loads((out/'live/analysis.json').read_text());probe=json.loads((out/'actuator/analysis.json').read_text())
    assert live['validation']==probe['validation']=='passed' and len(live['runs'])==10 and probe['episodes']==32
    for directory in ['live','actuator']:
        manifest=json.loads((out/directory/'manifest.json').read_text())
        for n,h in manifest['source_sha256'].items():
            assert sha(root/n)==h,n
            if n in deps:assert deps[n]==h
            deps[n]=h
    prior=json.loads((root/'results/live_repair_closed_loop_20261001/source_manifest.json').read_text())
    for n,h in prior['source_sha256'].items():assert sha(root/n)==h,n;deps[n]=h
    for directory in ['frontier','repair']:
        manifest=json.loads((out/directory/'analysis.json').read_text())
        for n,h in manifest['source_sha256'].items():assert sha(Path(__file__).parent/n)==h,n
    for directory in ['inherited','one_thread']:
        manifest=json.loads((out/directory/'analysis.json').read_text());assert sha(Path(__file__).with_name('profile_source.py'))==manifest['source_sha256']
    for p in Path(__file__).resolve().parent.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:deps[str(p.relative_to(root))]=sha(p)
    model_path=root/'results/actuation_calibration_20261001/analysis/models.json';model_sha=sha(model_path)
    assert model_sha==json.loads((out/'live/manifest.json').read_text())['model_sha256']
    for n in ['mobi-online-evidence-cleanup.json','mobi-online-evidence-server.json','mobi-actuator-probe-cleanup.json','mobi-actuator-probe-server.json']:
        shutil.copy2(Path('/mnt/c/Users/Administrator')/n,out/n)
    for n in ['mobi-online-evidence-cleanup.json','mobi-actuator-probe-cleanup.json']:assert not json.loads((out/n).read_bytes())['running']
    manifest=dict(host=socket.gethostname(),source_sha256=deps,model_file_sha256={str(model_path.relative_to(root)):model_sha},validation='passed',raw_live_inputs=sum(r['input_frames'] for r in live['runs']),live_physics_ticks=sum(r['physics_ticks'] for r in live['runs']),actual_commands=sum(r['issued'] for r in live['runs']),actuator_episodes=32,actuator_physics_ticks=probe['physics_ticks'],scope='Finite post-analysis optimization, fresh synchronous modeled-link control and separate actuator diagnostics; full research goal remains incomplete.')
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    archive=Path('/mnt/c/Users/Administrator/mobi-online-evidence-results.tgz')
    with tarfile.open(str(archive),'w:gz') as t:t.add(out,arcname=str(out.relative_to(root)))
    print(json.dumps(dict(files=len(files),source_files=len(deps),archive_bytes=archive.stat().st_size)))


if __name__=='__main__':main()
