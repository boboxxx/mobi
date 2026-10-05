#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];Q=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();m=json.loads((Q/'manifest.json').read_text())
 for section in ('files','inputs'):
  for name,digest in m[section].items():assert sha(R/name)==digest,name
 original=(R/'experiments/useful_expiry_certificate_20261004/plot_complete.py').read_text();expected=original.replace("E=Path(__file__).resolve().parent;P=R/'results'/E.name","E=R/'experiments/useful_expiry_certificate_20261004';P=R/'results'/E.name;Q=Path(__file__).resolve().parent").replace('risk+.005','risk-.006').replace("ha='center',fontsize=9);axes[1].text","ha='center',va='top',color='white',fontsize=9);axes[1].text").replace("ax.legend(fontsize=8,loc='upper left')","ax.legend(fontsize=8,loc=('center left' if ax is axes[2] else 'upper left'))").replace("out=P/'all_methods.png'","out=Q/'all_methods_layout.png'").replace("target=P/'figure_inputs.json'","target=Q/'figure_layout_inputs.json'");assert (Q/'plot_layout.py').read_text()==expected
 d=json.loads((Q/'episode_endpoint_check.json').read_text());assert len(d['cases'])==612 and d['frozen_progress_endpoint_step']==100 and d['drive_steps']==60 and d['brake_steps']==40
 for name,h in d['input_sha256'].items():assert sha(R/name)==h
 assert all(c['different_observed_labels']==0 for c in d['cells'])
 receipt=json.loads((Q/'figure_layout_inputs.json').read_text());assert receipt['figure_sha256']==sha(Q/'all_methods_layout.png')
 result=dict(manifest_sha256=sha(Q/'manifest.json'),figure_sha256=sha(Q/'all_methods_layout.png'),original_data_and_plot_calculations_unchanged=True,all_612_recorded_endpoint_labels_checked=True,frozen_endpoint_step=100,observed_three_and_five_second_threshold_labels_agree=True,no_new_three_second_population_guarantee=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('LAYOUT_AND_ENDPOINT_SUPPLEMENT_VERIFIED')
if __name__=='__main__':main()
