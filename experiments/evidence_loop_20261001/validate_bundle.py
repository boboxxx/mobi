#!/usr/bin/env python3
import argparse,hashlib,json,socket
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;src=Path(__file__).resolve().parent;root=src.parents[1];deps={}
    for sub in ['initial','compressed','fast']:
        m=json.loads((p/sub/'manifest.json').read_text())
        for n,h in m['source_sha256'].items():assert sha(root/n)==h,n;deps[n]=h
        assert sha(src/'PROTOCOL.md')==m['protocol_sha256']
        assert sha(root/'results/actuation_calibration_20261001/analysis/models.json')==m['model_sha256']
    for name in ['compression_profile.json','repair/report.json']:
        for n,h in json.loads((p/name).read_text())['source_sha256'].items():assert sha(src/n)==h,n
    for q in src.iterdir():
        if q.is_file():deps[str(q.relative_to(root))]=sha(q)
    q=root/'results/actuation_calibration_20261001/analysis/models.json';deps[str(q.relative_to(root))]=sha(q)
    audit=json.loads((p/'analysis.json').read_text());assert audit['validation']=='passed' and audit['analysis_sha256']==sha(src/'analyze.py');rows=sum([audit[k] for k in ['first','corrected','fast']],[])
    assert sum(x['raw_cloud_packet_replays'] for x in rows)==214
    assert sum(x['verified_physics_ticks'] for x in rows)==1813
    assert sum(x['drive_decisions'] for x in rows)==120 and sum(x['issued'] for x in rows)==0
    assert sum(1 for q in p.glob('*/*/clouds/*.npz'))==214
    assert json.loads((p/'server_cleanup.json').read_text())['own_server_remaining'] is False
    assert 'Ran 8 tests' in (p/'tests_final.log').read_text() and 'OK' in (p/'tests_final.log').read_text()
    repair=json.loads((p/'repair/report.json').read_text());assert len(repair['rows'])==8 and repair['all_proofs_fully_verified'] and repair['current_ray_provenance_verified']
    (p/'dependencies.json').write_text(json.dumps(deps,indent=2,sort_keys=True)+'\n')
    summary=dict(host=socket.gethostname(),raw_frame_replays=214,physics_ticks=1813,driving_decisions=120,forward_commands=0,tests=8,greedy_pairs=24,post_analysis_repair_pairs=8,server_stopped=True,validation='passed',scope='Archive integrity plus existing full replay audit; no successful driving or physical safety claim.')
    (p/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
