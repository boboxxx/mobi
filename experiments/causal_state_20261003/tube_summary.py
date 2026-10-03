#!/usr/bin/env python3
import argparse,hashlib,json,statistics
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'tube_sheng.json').read_bytes());audit=json.loads((p/'tube_audit_sheng.json').read_bytes());primary=json.loads((p/'summary_sheng.json').read_bytes());assert audit['tube_sha256']==sha(p/'tube_sheng.json');out=[]
    for rate in (20000000,2000000):
        for method in ('union','lossless_centers','full_xyz','fixed200'):
            tt=[r for r in audit['trace_checks'] if r['bitrate']==rate and r['method']==method];assert len(tt)==360;rr=[r for r in d['rows'] if r['split']=='test'];base=next(c for c in primary['comparisons'] if c['bitrate']==rate and c['method']==method)
            out.append(dict(bitrate=rate,method=method,grants=sum(t['grants'] for t in tt),scheduled_queries=11520,primary_grants=base['grants'],paired_grant_change=sum(t['grants'] for t in tt)-base['grants'],wire_bytes=sum(t['wire_bytes'] for t in tt),observed_disc_occupied_grants=sum(t['observed_disc_occupied_grants'] for t in tt),median_test_packet_bytes=statistics.median(r['methods'][method]['wire_bytes'] for r in rr),median_test_source_us=statistics.median(r['methods'][method]['source_us'] for r in rr),median_test_receiver_us=statistics.median(r['methods'][method]['receiver_us'] for r in rr),classes=[dict(blueprint=bp,grants=sum(t['grants'] for t in tt if t['blueprint']==bp),scheduled_queries=1920) for bp in d['registry']]))
    result=dict(total=dict(scheduled_calibration_episodes=570,scheduled_test_episodes=360,test_future_excluded_episodes=sum(c['future_excluded_episodes'] for c in audit['summary']),joint_calibration_confidence_lower=primary['total']['joint_calibration_confidence_lower'],future_pairs=audit['future_pairs'],packet_checks=audit['packet_checks'],analytic_age_checks=audit['analytic_age_checks']),classes=audit['summary'],comparisons=out,source_sha256=sha(Path(__file__)),tube_sha256=sha(p/'tube_sheng.json'),tube_audit_sha256=sha(p/'tube_audit_sheng.json'),primary_summary_sha256=sha(p/'summary_sheng.json'),scope='Paired finite future-SNAPSHOT prediction tube versus primary state/motion model with separately measured paid timing. No continuous physical or ego-driving guarantee, independent-query inference, or novelty claim.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['total']))
if __name__=='__main__':main()
