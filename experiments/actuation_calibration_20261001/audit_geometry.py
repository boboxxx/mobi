#!/usr/bin/env python3
"""Independently reconstruct recorded CARLA corners using Euler rotations.

CARLA 0.9.15 Transform.h and BoundingBox.h specify Rz(yaw) Ry(-pitch)
Rx(-roll), then translation, including the bounding box's local transform.
"""
import argparse,csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np


def rotation(pitch,yaw,roll):
    p,y,r=map(math.radians,(pitch,yaw,roll));cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y);cr,sr=math.cos(r),math.sin(r)
    return np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])@np.array([[cp,0,-sp],[0,1,0],[sp,0,cp]])@np.array([[1,0,0],[0,cr,sr],[0,-sr,cr]])


def vertices(body,state):
    corners=np.array([[x,y,z] for x in [-body['half_length'],body['half_length']] for y in [-body['half_width'],body['half_width']] for z in [-body['half_height'],body['half_height']]])
    local=corners@rotation(**body['rotation']).T+np.array([body['offset_x'],body['offset_y'],body['offset_z']])
    return local@rotation(state['pitch'],state['yaw'],state['roll']).T+np.array([state['x'],state['y'],state['z']])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=list(csv.DictReader((a.capture/'summary.csv').open()));count=0;maximum=0.;under=0.;pitch=roll=0.
    for row in rows:
        path=a.capture/'episodes'/(row['id']+'.json.gz');assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];record=json.loads(gzip.decompress(path.read_bytes()));body=record['body']
        for s in [record['initial']]+record['rows']:
            v=np.asarray(s['body_vertices']);d=float(np.abs(vertices(body,s)-v).max());assert d<.0002,(row['id'],s['frame'],d);maximum=max(maximum,d);count+=1
            if s.get('phase') in ['command','backup']:
                pitch=max(pitch,abs(s['pitch']));roll=max(roll,abs(s['roll']));local=(v-np.array([s['x'],s['y'],s['z']]))@rotation(0,s['yaw'],0);lo=np.array([body['offset_x']-body['half_length'],body['offset_y']-body['half_width']]);hi=np.array([body['offset_x']+body['half_length'],body['offset_y']+body['half_width']]);under=max(under,float(np.maximum(np.maximum(lo-local[:,:2],local[:,:2]-hi),0).max()))
    report=dict(episodes=len(rows),snapshot_corner_sets=count,corner_coordinate_max_error_m=maximum,yaw_only_max_missing_coordinate_extent_m=under,max_action_abs_pitch_deg=pitch,max_action_abs_roll_deg=roll,validation='passed',scope='Eight recorded corners independently reconstructed from full actor and local-box transforms; 0.2 mm numerical check, not a physical sensor-error bound.')
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
