#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'results/background_frontend_20261004';d=json.loads((P/'summary_sheng.json').read_bytes());body=json.loads((P/'body_support_sheng.json').read_bytes());parent=json.loads((ROOT/'results/prospective_expiry_20261003/analysis_sheng.json').read_bytes());x=np.arange(6);labels=['Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker'];plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42});fig,ax=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
old=[c['old_radius_um']/1e6 for c in d['classes']];new=[c['development_radius_um']/1e6 for c in d['classes']];ax[0].bar(x-.18,old,.36,label='Original centroid',color='#8094a6');ax[0].bar(x+.18,new,.36,label='Background centroid',color='#25827b');ax[0].set(ylabel='Descriptive max95 radius (m)',title='Background subtraction removes merging');ax[0].legend(fontsize=8)
ax[1].bar(x-.18,[c['variants'][0]['excluded_episodes'] for c in d['classes']],.36,label='Background centroid',color='#b96b4e');ax[1].bar(x+.18,[c['zero_slack_excluded_episodes'] for c in body['summary']],.36,label='All-point body support',color='#25827b');ax[1].set(ylabel='Excluded episodes / 60 planned per class',title='Smaller centroid radius is unreliable',ylim=(0,11));ax[1].legend(fontsize=8)
oldgeo=[]
for c in d['classes']:oldgeo.append(sum(b['lower_us']>=220000 for r in parent['rows'] if r['blueprint']==c['blueprint'] and r['split']=='test' and r['available'] for b in r['bounds']))
ax[2].bar(x-.18,oldgeo,.36,label='Original centroid',color='#8094a6');ax[2].bar(x+.18,[c['variants'][0]['geometric_horizons_at_least_220ms'] for c in d['classes']],.36,label='Background centroid',color='#b96b4e');ax[2].set(ylabel='Source-time horizons ≥ 220 ms / 720 planned',title='Geometric utility; fees not yet paid');ax[2].legend(fontsize=8)
for z in ax:z.set_xticks(x,labels,rotation=30,ha='right');z.grid(axis='y',alpha=.2);z.set_axisbelow(True)
fig.suptitle('Observation representation: preserve coverage before claiming expiry utility',fontsize=13)
fig.supxlabel('Reused-data development; no new risk qualification. All-point support expiry/paid utility remains uncomputed. Known class/body and fixed scene only.',fontsize=8)
fig.savefig(P/'background_frontend.png',dpi=180);fig.savefig(P/'background_frontend.pdf',metadata={'CreationDate':None,'ModDate':None})
