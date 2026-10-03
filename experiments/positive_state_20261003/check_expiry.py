#!/usr/bin/env python3
"""Posthoc truth reachability at BOTH start and end of each positive interval.

No outputs/thresholds change. Monotone disc reach makes the end sufficient for
the entire interval, conditional on the declared body and motion model only.
"""
import argparse
import hashlib
import json
from decimal import Decimal, ROUND_CEILING, localcontext
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    p = args.results
    analysis = json.loads((p / 'analysis_sheng.json').read_bytes())
    summary = json.loads((p / 'summary_sheng.json').read_bytes())
    truth = {r['id']: r for r in analysis['rows']}
    rows = []
    for r in summary['rows']:
        if r['split'] != 'test':
            continue
        original = truth[r['id']]
        with localcontext() as ctx:
            ctx.prec = 80
            ext = [Decimal.from_float(float(x)) for x in analysis['contract_body']['catalog'][r['blueprint']]]
            body = int((sum(x*x for x in ext).sqrt()*1000000).to_integral_value(rounding=ROUND_CEILING))
            for j, qx in enumerate((-6000000, 6000000)):
                net = r['modeled_remaining_us'][j]
                if net <= 0:
                    continue
                start = r['cost_us']
                end = start + net
                assert end == r['bounds'][j]['lower_us']
                x = Decimal.from_float(float(original['true_xy'][0]))*1000000-qx
                y = Decimal.from_float(float(original['true_xy'][1]))*1000000
                distance = (x*x+y*y).sqrt()
                def hit(us):
                    t = Decimal(us)/1000000
                    reach = body+750000+5000000*t+1500000*t*t
                    return x*x+y*y <= reach*reach
                gap = distance-body-750000
                true_contact = Decimal(0) if gap <= 0 else ((Decimal(25000000000000)+6000000*gap).sqrt()-5000000)/3000000*1000000
                start_hit, end_hit = hit(start), hit(end)
                assert not r['covered'] or not end_hit, r['id']
                rows.append(dict(id=r['id'], episode=r['episode'], blueprint=r['blueprint'], query=j,
                                 view_center_covered=r['covered'], start_us=start, end_us=end,
                                 true_model_contact_us=str(true_contact), reachable_at_start=start_hit,
                                 reachable_by_end=end_hit))
    out = dict(positive_queries=len(rows), reachable_at_start=sum(r['reachable_at_start'] for r in rows),
               reachable_by_end=sum(r['reachable_by_end'] for r in rows),
               affected_episodes=len({r['episode'] for r in rows if r['reachable_by_end']}),
               rows=rows, source_sha256=sha(Path(__file__)),
               analysis_sha256=sha(p/'analysis_sheng.json'), summary_sha256=sha(p/'summary_sheng.json'),
               scope='Posthoc full-positive-interval truth-center reachability under the same monotone body-disc/motion model. No actual motion, physical collision, live schedule or independent-query risk guarantee. Original start-only diagnostics preserved.')
    args.out.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
