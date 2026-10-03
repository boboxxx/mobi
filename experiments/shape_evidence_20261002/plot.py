#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();main=json.loads((a.results/'analysis_sheng.json').read_bytes())['summary'];follow=json.loads((a.results/'availability_followup/analysis_sheng.json').read_bytes())['summary']['walker.pedestrian.0001'];keys=[k for k in main if k.startswith('vehicle.')];labels=['Audi','Bicycle','Motorcycle','Sprinter','Tesla'];fig,ax=plt.subplots(1,3,figsize=(13,4.5),gridspec_kw={'width_ratios':[1.4,1.4,1]});colors=['#b95437','#167d8d'];w=.36;x=np.arange(len(keys))
    for j,method in enumerate(('full_only','joint')):
        counts=[main[k][method]['false_exclusion_episodes'] for k in keys];utility=[100*main[k][method]['translated_rejections']/main[k][method]['translated_total'] for k in keys]
        ax[0].bar(x+(j-.5)*w,counts,w,color=colors[j],label=('Full-only threshold','Joint calibration')[j]);ax[1].bar(x+(j-.5)*w,utility,w,color=colors[j]);ax[2].bar(j,follow[method]['false_exclusion_episodes'],.65,color=colors[j]);ax[2].text(j,follow[method]['false_exclusion_episodes']+.13,str(follow[method]['false_exclusion_episodes']),ha='center')
    for i in (0,1):ax[i].set_xticks(x);ax[i].set_xticklabels(labels,rotation=25,ha='right')
    ax[0].set_title('True-hypothesis exclusions');ax[0].set_ylabel('Episodes out of 20 per class');ax[0].set_ylim(0,7);ax[0].legend(frameon=False,fontsize=8)
    ax[1].set_title('Translated-hypothesis diagnostic');ax[1].set_ylabel('Rejected hypotheses (%)');ax[1].set_ylim(0,105)
    ax[2].set_title('Fresh pedestrian follow-up');ax[2].set_xticks([0,1]);ax[2].set_xticklabels(['Full-only','Joint']);ax[2].set_ylim(0,5.5);ax[2].set_ylabel('True-hypothesis exclusions');ax[2].text(.5,5,'19 available / 20 scheduled\n1 unavailable episode refused',ha='center',va='top',fontsize=8)
    for a0 in ax:a0.spines[['top','right']].set_visible(False);a0.grid(axis='y',alpha=.15);a0.set_axisbelow(True)
    fig.suptitle('Finite CARLA shape-evidence validation: risk and retained discrimination',fontsize=13)
    fig.text(.5,.015,'Translated boxes are truth-referenced diagnostics, not verified empty space. Zero observed exclusions is not a zero-risk guarantee.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.045,1,.94));fig.savefig(a.results/'shape_validation.png',dpi=170);fig.savefig(a.results/'shape_validation.pdf');plt.close(fig)
if __name__=='__main__':main()
