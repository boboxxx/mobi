#!/usr/bin/env python3
"""Preserve initial failures and verify corrections alter imports/layout only."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 for fn in ('matched_import_freeze.json','layout_freeze.json'):
  f=read(E/fn)
  for section in ('sources','inputs'):
   for n,h in f[section].items():assert sha(ROOT/n)==h,n
 old=(E/'matched.py').read_text();corrected=old.replace('from summarize import stats',"_summary_spec=importlib.util.spec_from_file_location('matched_fixed_local_summary',Path(__file__).resolve().parent/'summarize.py');_summary_module=importlib.util.module_from_spec(_summary_spec);_summary_spec.loader.exec_module(_summary_module);stats=_summary_module.stats").replace("freeze=read(E/'matched_freeze.json')","freeze=read(E/'matched_import_freeze.json')").replace('result=dict(planned_episodes=72',"result=dict(correction_freeze_sha256=sha(E/'matched_import_freeze.json'),planned_episodes=72")
 assert corrected==(E/'matched_complete.py').read_text()
 assert 'ImportError' in (P/'matched_sheng.log').read_text() and 'Tight layout not applied' in (P/'plot_initial_warning.txt').read_text()
 plot=(E/'plot.py').read_text().replace("out=P/'all_methods.png';receipt=P/'figure_inputs.json'","out=P/'all_methods_layout.png';receipt=P/'figure_layout_inputs.json'").replace("ax[1].set_ylabel('Completed episode forward progress (m)');","ax[1].set_ylim(-.01,max(.2,max(v['completed_episode_forward_m'].get('max',0) for v in s['cells'])+.2));ax[1].set_ylabel('Completed episode forward progress (m)');").replace("ax[1].set_title('All held-out episodes; certificate gate applied')","ax[1].set_title('All held-out episodes; certificate gate applied',fontsize=9)").replace("ax[0].set_title('180 planned certification episodes / method')","ax[0].set_title('180 planned certification episodes / method',fontsize=9)").replace("ax[2].set_title('24 unpaired planned test episodes / method')","ax[2].set_title('24 unpaired planned test episodes / method',fontsize=9)")
 assert plot==(E/'plot_complete.py').read_text()
 for fn,img in (('figure_inputs.json','all_methods.png'),('figure_layout_inputs.json','all_methods_layout.png')):
  f=read(P/fn)
  for n,h in f['input_sha256'].items():assert sha(ROOT/n)==h,n
  assert f['figure_sha256']==sha(P/img)
 m=read(P/'matched_verification.json');assert m['dual_host_bytes_identical'] and m['all_denominators_cross_checked'] and m['matched_sha256']==sha(P/'matched_sheng.json')
 result=dict(import_only_change_verified=True,layout_only_change_verified=True,original_failure_and_figure_preserved=True,matched_sha256=sha(P/'matched_sheng.json'),corrected_figure_sha256=sha(P/'all_methods_layout.png'),scope='Correction and figure byte audit; no safety, new statistical certificate or useful driving claim.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
