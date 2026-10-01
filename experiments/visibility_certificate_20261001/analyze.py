#!/usr/bin/env python3
"""Validate saved provenance and receiver proofs, then produce finite-run figures."""
import argparse, collections, csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from geometry import Profile, plane_witnesses
from proof_packet import QUANTUM, QUANT_ERROR, canonical
from renewal import verify_all
from run_study import CLASSES, write


def read(path):
    return list(csv.DictReader(path.open()))


def yes(row, key):
    return row[key] == 'True'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--no-plots', action='store_true')
    a = ap.parse_args(); root = a.results
    src = Path(__file__).parent
    for part in ['study2000', 'carla120', 'renewal', 'bundle']:
        m = json.loads((root / part / 'manifest.json').read_text())
        for name, digest in m['source_sha256'].items():
            assert hashlib.sha256((src / name).read_bytes()).hexdigest() == digest, (part, name)
    m = json.loads((root / 'study2000/manifest.json').read_text())
    assert hashlib.sha256((src / 'PROTOCOL.md').read_bytes()).hexdigest() == m['protocol_sha256']
    synthetic = read(root / 'study2000/synthetic.csv')
    assert len(synthetic) == 2000
    assert all(int(r['false_center_exclusions']) == 0 and int(r['expiry_overestimate']) == 0 for r in synthetic)
    frames = read(root / 'carla120/frames.csv')
    unique = {r['id']: r for r in frames}
    assert len(frames) == 480 and len(unique) == 120
    assert all(r['frame'] == r['sensor_frame'] and int(r['stale_frames']) == 0 for r in frames)
    clouds = sorted((root / 'carla120/clouds').glob('*.npz'))
    assert {p.stem for p in clouds} == set(unique)
    for p in clouds:
        d = np.load(p)
        assert d['xyz'].ndim == 2 and d['xyz'].shape[1] == 3 and np.isfinite(d['xyz']).all()
    checks = read(root / 'renewal/center_checks.csv')
    assert len(checks) == 320 and not any(yes(r, 'center_excluded') for r in checks)
    bundles = read(root / 'bundle/bundles.csv')
    assert len(bundles) == 232
    proof_count = 0
    for r in bundles:
        profiles, scopes = {}, {}
        for name in CLASSES:
            template = root / 'carla120/packets' / ('%s_%s_free_00_%s_%s_0.2.json' % (r['density'], r['layout'], r['thinning'], name))
            if template.exists():
                profiles[name] = Profile(**json.loads(template.read_bytes())['payload']['profile'])
                scopes[name] = r['id'] + ':' + name
        path = root / 'bundle/packets' / (r['id'] + '_' + r['thinning'] + '.json')
        payload = json.loads(path.read_bytes()) if path.exists() else {}
        blobs = {k: canonical(v) for k, v in payload.items()}
        eligible = set(profiles) == set(CLASSES)
        assert eligible == yes(r, 'template_available')
        assert bool(eligible and verify_all(blobs, profiles, scopes, .02, .05)) == yes(r, 'geometry_verified')
        assert bool(eligible and verify_all(blobs, profiles, scopes, float(r['modeled_total_age_s']), .05)) == yes(r, 'timing_budget_passed')
        if payload:
            assert len(path.read_bytes()) == int(r['packet_bytes'])
            d = np.load(root / 'carla120/clouds' / (r['id'] + '.npz'))
            w = plane_witnesses(d['xyz'][::int(r['thinning'])], d['origin'], d['query'], float(d['probe_z']))
            tree = cKDTree(w)
            for value in payload.values():
                points = np.asarray(value['payload']['witnesses']) * QUANTUM
                assert np.max(tree.query(points)[0]) <= QUANT_ERROR + 1e-9
                proof_count += 1
    assert not any(yes(r, 'geometry_verified') for r in bundles if r['scenario'] == 'near')
    assert json.loads((root / 'server_cleanup.json').read_text())['own_server_remaining'] is False
    cold = read(root / 'carla120/packet_results.csv')
    renewal = read(root / 'renewal/renewal.csv')
    accepted = [r for r in bundles if yes(r, 'timing_budget_passed')]
    groups = collections.defaultdict(list)
    for r in frames:
        if r['thinning'] == '1':
            groups[(r['density'],r['layout'],r['scenario'],r['model'])].append(r)
    geometry_rows = []
    for key, rs in sorted(groups.items()):
        geometry_rows.append(dict(zip(['density','layout','scenario','model'], key),
                                  count=len(rs), primary_ttl_s=np.mean([float(r['primary_ttl_s']) for r in rs]),
                                  selected_ttl_s=np.mean([float(r['chosen_ttl_s']) for r in rs])))
    write(root / 'geometry_summary.csv', geometry_rows)
    summary = dict(validation='passed', source_manifests_checked=4, raw_clouds=120, analytic_scenes=2000,
                   synthetic_positive=sum(float(r['validity_s'])>0 for r in synthetic),
                   false_center_exclusions=0, expiry_overestimates=0, actual_center_checks=len(checks),
                   stale_frames=0, serialized_current_ray_proofs_checked=proof_count,
                   cold=dict(attempts=len(cold), geometry=sum(yes(r,'geometry_verified') for r in cold), timing=sum(yes(r,'timing_budget_passed') for r in cold)),
                   per_class_renewal=dict(attempts=len(renewal), geometry=sum(yes(r,'geometry_verified') for r in renewal), timing=sum(yes(r,'timing_budget_passed') for r in renewal)),
                   bundle=dict(attempts=len(bundles), templates=sum(yes(r,'template_available') for r in bundles),
                               geometry=sum(yes(r,'geometry_verified') for r in bundles), timing=len(accepted),
                               near_rejected=sum(r['scenario']=='near' for r in bundles),
                               eligible_near_rejected=sum(r['scenario']=='near' and yes(r,'template_available') for r in bundles),
                               age_ms_min=float(min(float(r['modeled_total_age_s'])*1000 for r in accepted)),
                               age_ms_median=float(np.median([float(r['modeled_total_age_s'])*1000 for r in accepted])),
                               age_ms_max=float(max(float(r['modeled_total_age_s'])*1000 for r in accepted)),
                               sender_ms_median=float(np.median([float(r['sender_ms']) for r in accepted])),
                               receiver_ms_median=float(np.median([float(r['receiver_ms']) for r in accepted])),
                               bytes_min=min(int(r['packet_bytes']) for r in accepted), bytes_max=max(int(r['packet_bytes']) for r in accepted)),
                   scope='Conditional geometric bounds. Repeated static frames, no natural-scene probability or closed-loop driving claim.')
    (root / 'analysis.json').write_text(json.dumps(summary, indent=2)+'\n')
    if not a.no_plots:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
        labels=[]; primary=[]; selected=[]
        for density in ['base','dense']:
            for layout in ['0','1']:
                entries=[r for r in geometry_rows if r['density']==density and r['layout']==layout and r['scenario']=='free']
                labels.append(density+' / view '+layout)
                primary.append(min(r['primary_ttl_s'] for r in entries)*1000)
                selected.append(min(r['selected_ttl_s'] for r in entries)*1000)
        x=np.arange(4)
        axs[0].bar(x-.18,primary,.36,label='Primary 0.1 m grid',color='#5b7898')
        axs[0].bar(x+.18,selected,.36,label='With declared refinement',color='#26917e')
        axs[0].set_xticks(x);axs[0].set_xticklabels(labels,rotation=18,ha='right')
        axs[0].set_ylabel('Two-class geometric expiry (ms)');axs[0].legend(fontsize=8)
        axs[0].set_title('Free scenes, full rays; fixed physical bounds')
        for layout, color in [('0','#26917e'),('1','#5b7898')]:
            vals=[(float(r['modeled_total_age_s'])+.05)*1000 for r in accepted if r['layout']==layout]
            axs[1].plot(np.arange(len(vals)),sorted(vals),'o-',ms=3,label='Dense view '+layout,color=color)
        axs[1].axhline(200,color='#b84a4a',ls='--',label='200 ms validity')
        axs[1].set_ylim(0,220);axs[1].set_xlabel('Sorted repeated static frame');axs[1].set_ylabel('Age + 50 ms action (ms)')
        axs[1].set_title('38 two-class renewals, measured CPU + modeled link');axs[1].legend(fontsize=8)
        fig.tight_layout();fig.savefig(root/'findings.png',dpi=180);fig.savefig(root/'findings.pdf');plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
