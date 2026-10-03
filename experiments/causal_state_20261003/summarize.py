#!/usr/bin/env python3
import argparse,hashlib,json,statistics
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results
    d=json.loads((p/'analysis_sheng.json').read_bytes());audit=json.loads((p/'audit_sheng.json').read_bytes());assert audit['analysis_sha256']==sha(p/'analysis_sheng.json');classes=audit['summary'];groups=[]
    for rate in (20000000,2000000):
        for method in ('union','lossless_centers','full_xyz','fixed200'):
            traces=[t for t in audit['trace_checks'] if t['bitrate']==rate and t['method']==method];assert len(traces)==360
            rr=[r for r in d['rows'] if r['split']=='test'];rates=[]
            for bp in d['registry']:
                tt=[t for t in traces if t['blueprint']==bp];assert len(tt)==60
                rates.append(dict(blueprint=bp,grants=sum(t['grants'] for t in tt),scheduled_queries=1920,wire_bytes=sum(t['wire_bytes'] for t in tt)))
            groups.append(dict(bitrate=rate,method=method,grants=sum(t['grants'] for t in traces),scheduled_queries=11520,wire_bytes=sum(t['wire_bytes'] for t in traces),truth_model_reachable_grants=sum(t['truth_model_reachable_grants'] for t in traces),observed_disc_occupied_grants=sum(t['observed_disc_occupied_grants'] for t in traces),median_test_packet_bytes=statistics.median(r['methods'][method]['wire_bytes'] for r in rr),median_test_source_us=statistics.median(r['methods'][method]['source_us'] for r in rr),median_test_receiver_us=statistics.median(r['methods'][method]['receiver_us'] for r in rr),classes=rates))
    result=dict(total=dict(scheduled_calibration_episodes=570,scheduled_test_episodes=360,captured_frames=audit['captured_frames'],stored_rays=audit['stored_rays'],original_reported_rays=audit['original_reported_rays'],test_excluded_episodes=sum(c['false_exclusion_episodes'] for c in classes),test_captured_episodes=sum(c['captured_test_episodes'] for c in classes),test_available_frames=sum(c['available_frames'] for c in classes),test_captured_frames=sum(c['captured_frames'] for c in classes),scheduled_test_frames=2160,joint_calibration_confidence_lower=audit['joint_calibration_confidence_lower'],motion_checks=audit['motion_checks'],motion_failures=audit['motion_failures'],body_corner_positive_excess_snapshots=audit['body_corner_positive_excess_snapshots'],max_body_corner_excess_um=audit['max_body_corner_excess_um']),classes=classes,comparisons=groups,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),scope='Fixed-calibration max95 tolerance statement under iid episode law; per-frame causal outputs, shared FIFO costs and source-aged query windows. Correlated queries and snapshot-only physical audit. Full scene inventory, actual link/ego closed loop and MobiCom novelty remain unestablished.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['total']))
if __name__=='__main__':main()
