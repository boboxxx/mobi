#!/usr/bin/env python3
import argparse,hashlib,json,statistics
from pathlib import Path
E=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');audit=read(p/'audit_sheng.json');assert audit['analysis_sha256']==sha(p/'analysis_sheng.json');out=[]
    for bp in d['catalog']:
        ee=[e for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(ee)==60;test=[r for r in d['rows'] if r['blueprint']==bp and r['split']=='test'];variants=[]
        for i,shift in enumerate((0.,.001,.01)):
            vv=[r['variants'][i] for r in test];bad={r['episode_id'] for r in test if not r['variants'][i]['covered']};positive=sum(b[0]>=220000 for v in vv if v['available'] for b in v['bounds']);positive_bad=sum(b[0]>=220000 for r in test if r['episode_id'] in bad and r['variants'][i]['available'] for b in r['variants'][i]['bounds']);changes=sum(x['variants'][i]['proposals_changed'] for x in audit['frame_checks'] if x['blueprint']==bp and x['split']=='test');costs=[v['source_us'] for v in vv if v['source_us'] is not None]
            variants.append(dict(shift_m=shift,captured_frames=len(vv),scheduled_frames=360,available_frames=sum(v['available'] for v in vv),refused_captured_frames=sum(not v['available'] for v in vv),excluded_episodes=len(bad),excluded_episode_ids=sorted(bad),geometric_horizons_at_least_220ms=positive,geometric_positive_on_excluded_episodes=positive_bad,changed_proposal_frames=changes,target_returns=sum(v['target_returns'] for v in vv),target_returns_removed=sum(v['target_returns_removed'] for v in vv),median_extraction_us=statistics.median(costs) if costs else None,max_extraction_us=max(costs) if costs else None))
        out.append(dict(blueprint=bp,old_radius_um=d['old_registry'][bp]['radius_um'],development_radius_um=d['registry'][bp]['radius_um'],captured_test_episodes=sum(e['status']=='captured' for e in ee),scheduled_test_episodes=60,variants=variants))
    result=dict(classes=out,fit_scans=audit['fit_scans'],static_voxels=audit['static_voxels'],setup_wire_bytes=d['setup_wire_bytes'],analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),source_sha256=sha(Path(__file__)),scope='Geometric source-age>=220ms counts only, no paid or received grants. Changed frontend on reused inspected data, descriptive max95 radii without prospective risk guarantee. Fixed-shift synthetic diagnostics, no noise-distribution bound.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
