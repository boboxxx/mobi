#!/usr/bin/env python3
"""Assemble the completed sheng runs without modifying capture sources/data."""
import hashlib, json, shutil, socket, tarfile
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[2]
    out=root/'results/live_repair_closed_loop_20261001'
    out.mkdir(exist_ok=True)
    for source,target in [('live_repair_fresh_20261001','capture'),
                          ('live_repair_20261001','failed_attempt'),
                          ('expiry_frontier_20261001','frontier')]:
        source_path=root/'results'/source; target_path=out/target
        if target_path.exists():
            def inventory(path):
                return {str(f.relative_to(path)):hashlib.sha256(f.read_bytes()).hexdigest()
                        for f in path.rglob('*') if f.is_file()}
            assert inventory(source_path)==inventory(target_path), 'Partial archive differs from source'
        else:shutil.copytree(source_path,target_path)
    logs=out/'logs';logs.mkdir(exist_ok=True)
    for name in ['live_repair_20261001.log','live_repair_fresh_20261001.log',
                 'live_repair_fresh_20261001_analysis.log','expiry_frontier_20261001.log',
                 'expiry_frontier_tests_20261001.log','live_repair_tests_20261001.log',
                 'live_repair_prior_tests_20261001.log','live_repair_deadline_tests_20261001.log','live_repair_preflight.json']:
        shutil.copy2(root/'results'/name,logs/name)
    for name in ['mobi-live-repair-cleanup.json','mobi-live-repair-failed-cleanup.json',
                 'mobi-live-repair-server.json']:
        shutil.copy2(Path('/mnt/c/Users/Administrator')/name,out/name)
    assert not json.loads((out/'mobi-live-repair-cleanup.json').read_bytes())['running']
    deps={}
    for name in ['capture/manifest.json','frontier/analysis.json']:
        for path,digest in json.loads((out/name).read_text())['source_sha256'].items():
            assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
            if path in deps:assert deps[path]==digest
            deps[path]=digest
    for directory in ['experiments/live_repair_20261001','experiments/expiry_frontier_20261001']:
        for f in (root/directory).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:
                deps[str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
    (out/'source_manifest.json').write_text(json.dumps(dict(host=socket.gethostname(),source_sha256=deps),indent=2)+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='SHA256SUMS')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(out))+'\n' for f in files))
    archive=Path('/mnt/c/Users/Administrator/mobi-live-repair-results.tgz')
    with tarfile.open(str(archive),'w:gz') as t:t.add(out,arcname=str(out.relative_to(root)))
    print(json.dumps(dict(archive=str(archive),files=len(files),source_files=len(deps),bytes=archive.stat().st_size)))


if __name__=='__main__':main()
