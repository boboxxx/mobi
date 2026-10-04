#!/usr/bin/env python3
"""Standalone scientific comparison; no retiming or model selection."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
METHODS=('active','hull','points','raw');LABELS=('Active constraints','Exact hull','All component points','Stored XYZ')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'summary_sheng.json').read_bytes());fig,axs=plt.subplots(2,2,figsize=(12,8));colors=['#235789','#f1a208','#42a58d','#a34242'];x=np.arange(4)
 for ax,rate in zip(axs[0],(20000000,2000000)):
  warm=next(r for r in d['policies'] if r['rate']==rate and r['startup']=='warm');cold=next(r for r in d['policies'] if r['rate']==rate and r['startup']=='cold');ax.bar(x-.18,[warm['grants'][m] for m in METHODS],.36,label='Warm setup',color=colors);ax.bar(x+.18,[cold['grants'][m] for m in METHODS],.36,label='Cold, setup paid',color=colors,alpha=.45,hatch='//');ax.set_xticks(x);ax.set_xticklabels(LABELS,rotation=13,ha='right');ax.set_ylabel('Granted actions / 11,520 planned queries');ax.set_title('%d Mbps; source age and three FIFOs'%(rate//1000000));ax.legend(fontsize=8)
 cls=d['classes'];labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Pedestrian'];ax=axs[1,0];xx=np.arange(6)
 for i,m in enumerate(('active','hull','points')):ax.plot(xx,[r['methods'][m]['wire_bytes']['median'] for r in cls],marker='o',label=LABELS[METHODS.index(m)],color=colors[i])
 ax.set_xticks(xx);ax.set_xticklabels(labels,rotation=13);ax.set_yscale('log');ax.set_ylabel('Median actual compressed bytes');ax.set_title('Source body-support representations');ax.legend(fontsize=8)
 ax=axs[1,1];ax.bar(xx,[r['expiry_gap_to_truth_oracle_us']['p95']/1000 for r in cls],color='#235789');ax.set_xticks(xx);ax.set_xticklabels(labels,rotation=13);ax.set_ylabel('P95 source lifetime gap (ms)');ax.set_title('True-center isotropic oracle; 500 ms cap')
 fig.suptitle('Body-support expiry: reused fixed-scene development corpus',fontsize=14);fig.text(.5,.015,'Measured maxima are not WCET. No fresh risk qualification, unknown-inventory guarantee or physical closed-loop claim.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.035,1,.96));fig.savefig(p/'body_expiry.png',dpi=180);fig.savefig(p/'body_expiry.pdf');plt.close(fig)
if __name__=='__main__':main()
