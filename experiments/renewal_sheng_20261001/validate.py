#!/usr/bin/env python3
"""Check archived execution artifacts and their source hashes, without reruns."""
import csv
import hashlib
import json
from pathlib import Path


def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def main():
    code=Path(__file__).resolve().parent;root=code.parents[1]/'results/renewal_sheng_20261001'
    hashes=0;counts={};packaging_metadata=[]
    for sub,expected,key in [('main38500',38500,'code_sha256'),('stationary5500',5500,'source_sha256')]:
        manifest=json.loads((root/sub/'manifest.json').read_text())
        assert manifest['host']=='DESKTOP-UGDDO8T'
        for name,digest in manifest[key].items():
            if name.startswith('._'):
                packaging_metadata.append(name)
                continue
            assert hashlib.sha256((code/name).read_bytes()).hexdigest()==digest,name
            hashes+=1
        rows=read(root/sub/'per_episode.csv');assert len(rows)==expected
        assert len({(r['config'],r['method'],r['seed']) for r in rows})==expected
        counts[sub]=len(rows)
    rows=read(root/'main38500/per_episode.csv');lookup={(r['config'],r['method'],r['seed']):r for r in rows}
    metrics=['valid_fraction','claimed_fraction','false_valid_fraction','missed_valid_fraction','sent_messages','modeled_bytes']
    assert all(lookup['heterogeneous','stochastic_mpc3',str(s)][m]==lookup['heterogeneous','group_refresh',str(s)][m]
               for s in range(500) for m in metrics)
    frames=read(root/'carla_coverage_v4/frames.csv');assert len(frames)==320
    assert len({r['frame'] for r in frames})==80
    assert all(r['frame']==r['sensor_frame'] and r['stale_frames']=='0' for r in frames)
    manifest=json.loads((root/'carla_coverage_v4/manifest.json').read_text())
    assert manifest['source_sha256']==hashlib.sha256((code/'carla_coverage_gate.py').read_bytes()).hexdigest()
    assert manifest['primary_gate_passed'] is False
    cleanup=json.loads((root/'cleanup_world.json').read_text())
    assert cleanup==dict(remaining_vehicles=0,remaining_sensors=0,synchronous_mode=False)
    windows=json.loads((root/'cleanup_windows.json').read_text(encoding='utf-8-sig'))
    assert windows['remaining_carla_processes']==0
    report=dict(episode_counts=counts,unique_episode_keys=True,source_hashes_matched=hashes+1,
                excluded_appledouble_metadata=packaging_metadata,
                heterogeneous_primary_metrics_identical=True,carla_measured_world_frames=80,
                carla_analysis_rows=320,carla_frame_ids_match=True,carla_stale_frames=0,
                primary_coverage_gate_passed=False,world_cleanup=cleanup,remaining_carla_processes=0,
                scope='Artifact integrity checks; not proof of scientific novelty or driving safety.')
    (root/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
