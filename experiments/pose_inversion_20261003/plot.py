#!/usr/bin/env python3
import argparse,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
from scipy.spatial import ConvexHull
from audit import ROOT,rotation
def polygon(pose,e,road):
    corners=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)]);xy=((corners*np.array(e))@(road.T@rotation(pose[3:])).T+pose[:3])[:,:2];return xy[ConvexHull(xy).vertices]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;bank=json.loads((p/'witness_bank_sheng.json').read_bytes());sources={s['case']:s for s in json.loads((p/'replay/sources.json').read_bytes())};summary=json.loads((p/'summary.json').read_bytes());fig,axes=plt.subplots(1,3,figsize=(14,4.8),gridspec_kw={'width_ratios':[1.25,1.25,1]})
    for axis,overlap in zip(axes[:2],[False,True]):
        w=next(w for w in bank['candidates'] if w['accepted_by_stride']['1'] and w['upper_us']==0 and w['bounding_box_overlap']==overlap);s=sources[w['case']];e=s['extent'];road=np.array(s['road_rotation']);truth=next(r for r in json.loads((ROOT/s['source_record']).read_bytes()) if r.get('id')==s['source_id']);truepose=np.r_[road.T@(np.array(truth['center'])-s['anchor']),np.deg2rad(truth['actor_transform']['rotation'])];pose=np.array(w['pose']);query=np.array([-6 if w['query_index']==0 else 6,0]);axis.add_patch(Polygon(polygon(truepose,e,road),color='#277da8',alpha=.23,label='Actual bbox (audit)'));axis.add_patch(Polygon(polygon(pose,e,road),color='#d37929',alpha=.3,label='Accepted pose bbox'));axis.add_patch(Circle(pose[:2],np.linalg.norm(e),fill=False,color='#d37929',linestyle='--',label='Disc abstraction'));axis.add_patch(Circle(query,.75,color='#b94d50',alpha=.35,label='Task region'))
        with np.load(ROOT/s['source_cloud']) as z:
            raw=z['raw'];own=raw[raw['id']==truth['actor_id']];world=np.c_[own['x'],own['y'],own['z']].astype(float)@z['transform'][:3,:3].T+z['origin'];local=(world-s['anchor'])@road;axis.scatter(local[:,0],local[:,1],s=2,color='#277da8',alpha=.5)
        axis.set_title(('Disc overlap only','Bounding-box overlap')[int(overlap)]+'\n'+s['blueprint'].split('.')[-1],fontsize=11);xx=np.r_[truepose[0],pose[0],query[0]];yy=np.r_[truepose[1],pose[1],query[1]];margin=np.linalg.norm(e)+.5;axis.set_xlim(xx.min()-margin,xx.max()+margin);axis.set_ylim(yy.min()-margin,yy.max()+margin);axis.set_aspect('equal');axis.set_xlabel('Road longitudinal offset (m)');axis.set_ylabel('Lateral offset (m)');axis.grid(alpha=.15)
    axes[0].legend(fontsize=7,loc='best',frameon=False)
    budget=summary['variants']['replay']['by_budget'];values=[budget[str(s)]['wire_bytes']/1000 for s in (16,4,1)];axes[2].bar(['1/16','1/4','Full'],values,color=['#3a8d8c','#4477aa','#b94d50']);axes[2].axhline(650,color='#555',ls='--',lw=1);axes[2].text(.05,665,'500 ms cap minus fixed reserves\n650 kB ceiling before computation',fontsize=8);axes[2].set_ylim(0,1150);axes[2].set_title('Modeled 20 Mbps link');axes[2].set_ylabel('Actual packet size (kB)');axes[2].set_xlabel('Received raw-return budget')
    for i,v in enumerate(values):axes[2].text(i,v+15,'%.1f'%v,ha='center',fontsize=9)
    fig.suptitle('Retaining the true hypothesis does not establish useful expiry',fontsize=14);fig.text(.5,.02,'Accepted poses survive the full nested budget. Bbox overlap is not a physical mesh collision. Blue returns use labels for this audit illustration only.',ha='center',fontsize=8);fig.tight_layout(rect=(0,.05,1,.92));fig.savefig(p/'pose_counterexamples.png',dpi=170);fig.savefig(p/'pose_counterexamples.pdf');plt.close(fig)
if __name__=='__main__':main()
