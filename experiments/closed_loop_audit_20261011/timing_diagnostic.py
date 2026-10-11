"""Post-result timing explanation only. No action is granted or rerun."""
import argparse
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'experiments/closed_loop_motion_20261011'))
import runtime as R

parser = argparse.ArgumentParser()
parser.add_argument('--capture', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
outcomes = json.loads((args.capture/'outcomes.json').read_bytes())
episodes = []
for outcome in outcomes:
    data = json.loads(gzip.decompress((args.capture/outcome['file']).read_bytes()))
    if outcome['status'] != 'captured':
        continue
    ego_radius = R.A.pose.enclosing_radius_um(data['body']['extent'])
    summary = dict(id=outcome['id'], method=data['request']['method'], motion=data['request']['motion'],
        raw_gate_allowed=0, selected=0, overrun_rows=0, first_refusal=None,
        issued_go_overruns=0, issued_go_overruns_still_within_realized_envelope=0,
        pre_refusal_missing_evidence=0, pre_refusal_expiry_denials=0)
    previous_refused = False
    for row in data['rows']:
        fee = sum(row[k] for k in ('receiver_fee_us', 'query_fee_us', 'command_fee_us'))
        gate = row['gate']
        deadline_room = None if gate['source_us'] is None else gate['source_us']+gate['expiry_us']-row['now_us']-300000-fee
        body_room_num = (2500000-ego_radius-20000)*1000000-750000*(300000+fee)
        realized_ok = deadline_room is not None and deadline_room >= 0 and body_room_num >= 0
        summary['raw_gate_allowed'] += int(gate['allowed'])
        summary['selected'] += int(row['engineering_go'])
        summary['overrun_rows'] += int(fee > 20000)
        if row['engineering_go'] and fee > 20000:
            summary['issued_go_overruns'] += 1
            summary['issued_go_overruns_still_within_realized_envelope'] += int(realized_ok)
        if row['episode_refused'] and not previous_refused:
            summary['first_refusal'] = dict(step=row['step'], engineering_go=row['engineering_go'],
                domain_ok=row['domain_ok'], measured_total_fee_us=fee, raw_gate=gate,
                actual_cost_deadline_room_us=deadline_room,
                realized_cost_and_body_envelope_fit=bool(realized_ok))
        if not previous_refused and row['step'] < 600 and not row['reached'] and not gate['allowed']:
            summary['pre_refusal_missing_evidence'] += int(gate['source_us'] is None)
            summary['pre_refusal_expiry_denials'] += int(gate['source_us'] is not None)
        previous_refused = row['episode_refused']
    episodes.append(summary)
result = dict(scope='post-result explanation using realized control fee; not available before issuing command, not a prospective guarantee or corrected rollout',
    episodes=episodes, summary={key:sum(ep[key] for ep in episodes) for key in ('overrun_rows','issued_go_overruns','issued_go_overruns_still_within_realized_envelope','pre_refusal_missing_evidence','pre_refusal_expiry_denials')})
args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result['summary'], sort_keys=True))
