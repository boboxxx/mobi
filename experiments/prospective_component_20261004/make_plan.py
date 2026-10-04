"""Portable integer-grid independent law, fixed before any new capture."""
import json
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent
CATALOG=json.loads((E/'catalog.json').read_bytes());BLUEPRINTS=list(CATALOG)
def scene(rng,bp,split,index,seed,selected=None):
    x=int(rng.randint(-8000000,8000001));y=int(rng.randint(-4000000,4000001));yaw=int(rng.randint(0,360000));speed=int(rng.randint(500000,1800001) if bp.startswith('walker.') else rng.randint(1000000,3000001))
    result=dict(id='freshcomponent_'+bp.replace('.','_')+'_'+split+'_%04d'%index,blueprint=bp,split=split,index=index,seed=seed,longitudinal_m=x/1000000,lateral_m=y/1000000,yaw_deg=yaw/1000,target_speed_mps=speed/1000000,integer_scene=[x,y,yaw,speed])
    if selected is not None:result['selected_query_index']=int(selected)
    return result
def plan():
    rows=[]
    for ci,bp in enumerate(BLUEPRINTS):
        seed=2026104700+ci;rng=np.random.RandomState(seed)
        for i in range(260):rows.append(scene(rng,bp,'calibration',i,seed))
    rng=np.random.RandomState(2026104800);selector=np.random.RandomState(2026104801)
    for i in range(600):
        bp=BLUEPRINTS[int(rng.randint(0,6))];rows.append(scene(rng,bp,'certification',i,2026104800,selector.randint(0,32)))
    for ci,bp in enumerate(BLUEPRINTS):
        seed=2026104900+ci;rng=np.random.RandomState(seed)
        for i in range(60):rows.append(scene(rng,bp,'test',i,seed))
    assert len(rows)==2520 and len(set(r['id'] for r in rows))==2520
    return rows
if __name__=='__main__':
    p=E/'plan.json';assert not p.exists();p.write_text(json.dumps(plan(),indent=2)+'\n')
