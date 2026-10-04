#!/usr/bin/env python3
"""Post-test descriptive calibration bottlenecks; no fitting or threshold edits."""
from collections import Counter
from fractions import Fraction as F
from io_common import E, P, read, write, sha
from scores import error
from geometry import truth_integer
from observer import score, projections


def main():
    data = read(P / 'qualification_sheng.json')
    result = []
    for bp, thresholds in data['registry'].items():
        rows = [r for r in data['rows']
                if r['blueprint'] == bp and r['split'] == 'calibration']
        for family in ('local_mean', 'local_modes'):
            q = F(*thresholds[family])
            maxima = []
            components = Counter()
            for row in rows:
                hulls = row['hulls_cm']
                if not hulls:
                    components['empty_refusal'] += 1
                    continue
                p, denominator = truth_integer(row['true_xy'])
                pose = F(score(projections(hulls), data['catalog'][bp], p,
                               denominator), 10000)
                pred = row['prediction']
                learned = None
                if pred['status'] == 'supported':
                    if family == 'local_mean':
                        learned = F(error(pred['mean_um'], row['true_xy']),
                                    pred['single_scale_um'])
                    else:
                        learned = F(min(error(c, row['true_xy'])
                                        for c in pred['centers_um']),
                                    pred['modes_scale_um'])
                observed = pose if learned is None else max(pose, learned)
                assert observed == F(*row['scores'][family])
                binding = ('fallback_pose' if learned is None else
                           'tie' if learned == pose else
                           'pose' if pose > learned else 'learned')
                components[binding] += 1
                if observed == q:
                    maxima.append(dict(row_id=row['id'], episode_id=row['episode_id'],
                                       prediction_status=pred['status'], binding=binding,
                                       pose_score=[pose.numerator, pose.denominator],
                                       learned_score=None if learned is None else
                                       [learned.numerator, learned.denominator]))
            result.append(dict(blueprint=bp, family=family,
                               threshold=[q.numerator, q.denominator],
                               calibration_source_frames=len(rows),
                               score_binding_counts=dict(components),
                               maximum_rows=maxima))
    write(P / 'calibration_bottlenecks.json', dict(
        families=result,
        qualification_sha256=sha(P / 'qualification_sheng.json'),
        source_sha256=sha(E / 'diagnose.py'),
        scope='Post-test descriptive decomposition of already-frozen calibration scores. '
              'No new predictor, guard, scale, threshold or safety claim.'))
    print('FROZEN_CALIBRATION_BOTTLENECKS_DESCRIBED', flush=True)


if __name__ == '__main__':
    main()
