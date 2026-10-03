#!/usr/bin/env python3
"""Post-result extraction of the worst calibration rows; no policy changes."""
import argparse, hashlib, json
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    d = json.loads((a.results/'action_functional_sheng.json').read_bytes())
    primary = json.loads((a.results/'analysis_sheng.json').read_bytes())
    original = {r['id']: r for r in primary['rows']}
    cases = []
    for bp, fit in d['registry'].items():
        delta = fit['correction_us']
        if not delta:
            continue
        episodes = sorted(e['episode']['id'] for e in primary['episodes']
                          if e['episode']['blueprint'] == bp
                          and e['episode']['split'] == 'calibration'
                          and d['episode_scores'][e['episode']['id']] == delta)
        eid = episodes[0]
        rows = [r for r in d['rows'] if r['episode_id'] == eid]
        witnesses = [dict(source_id=r['id'], query=q,
                          base_age_us=b['lower_us'], grid_contact_age_us=g,
                          overstatement_us=max(0, b['lower_us']-g))
                     for r in rows if r['available']
                     for q, (b, g) in enumerate(zip(r['base_bounds'], r['grid_oracle_us']))
                     if b['lower_us'] >= 220000 and max(0, b['lower_us']-g) == delta]
        assert witnesses
        cases.append(dict(blueprint=bp, correction_us=delta, episode_id=eid,
                          calibration_witnesses=witnesses, task_rows=rows,
                          current_primary_rows=[original[r['id']] for r in rows],
                          capture_episode=next(e for e in primary['episodes']
                                               if e['episode']['id'] == eid)))
    result = dict(cases=cases, source_sha256=sha(Path(__file__)),
                  action_functional_sha256=sha(a.results/'action_functional_sheng.json'),
                  primary_analysis_sha256=sha(a.results/'analysis_sheng.json'),
                  scope='Post-result explanatory extraction of exact calibration-max witnesses; no new fit, policy, recapture or independent safety test.')
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps([dict(blueprint=c['blueprint'], episode_id=c['episode_id'],
                           correction_us=c['correction_us'], witnesses=c['calibration_witnesses'])
                      for c in cases]))

if __name__ == '__main__':
    main()
