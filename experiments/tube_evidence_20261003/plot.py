#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--summary',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();s=json.loads(a.summary.read_bytes());fig,axes=plt.subplots(1,3,figsize=(13,4.4));colors=['#286b98','#ce7b24','#30805a'];labels=['Saved capture','1 mm synthetic noise','10 mm synthetic noise']
 for sigma,color,label in zip([0,.001,.01],colors,labels):
  g=[g for g in s['groups'] if g['sigma']==sigma];x=[g['radius_um']/1000 for g in g];axes[0].plot(x,[g['median_wire_bytes']/1000 for g in g],'-o',color=color,label=label);axes[1].plot(x,[g['median_incremental_us']/1000 for g in g],'-o',color=color);axes[2].plot(x,[g['positive_incremental_remaining'] for g in g],'-o',color=color)
 axes[0].set_ylabel('Median current message (kB)');axes[0].set_yscale('log');axes[1].set_ylabel('Median receiver check (ms)');axes[1].set_yscale('log');axes[2].set_ylabel('Positive modeled remainder (of 12)');axes[2].set_ylim(-.2,12.2)
 for ax in axes:ax.set_xlabel('Advertised endpoint radius (mm)');ax.set_xticks([0,5,50]);ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False)
 fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.88),ncol=3,frameon=False);fig.suptitle('Bounded current evidence: communication, computation and usable time',y=.97,fontsize=14);fig.text(.5,.025,'Fixed saved-data matrix; modeled 20 Mbps link + 40 ms propagation/clock + 200 ms action reserve. No physical risk guarantee.',ha='center',fontsize=9);fig.subplots_adjust(left=.06,right=.99,bottom=.20,top=.74,wspace=.28);a.out.parent.mkdir(parents=True,exist_ok=True)
 for ext in ('png','pdf'):fig.savefig(str(a.out)+'.'+ext,dpi=180,bbox_inches='tight')
if __name__=='__main__':main()
