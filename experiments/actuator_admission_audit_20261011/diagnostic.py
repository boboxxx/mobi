"""Post-result descriptive diagnosis; never alters the frozen controller."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
result=[]
for o in json.loads((a.capture/'outcomes.json').read_bytes()):
 if o['status']!='captured':continue
 d=json.loads(gzip.decompress((a.capture/o['file']).read_bytes()));rows=d['rows'];speeds=[float(np.linalg.norm(r['own']['velocity'][:2])) for r in rows]
 result.append(dict(id=o['id'],speed_quantiles_mps=dict(zip(['p10','p50','p90','max'],map(float,np.quantile(speeds,[.1,.5,.9,1])))),first_goal_us=next((r['now_us'] for r in rows if r['reached']),None)))
a.out.write_text(json.dumps(dict(scope='post-result descriptive diagnosis, not an independent validation sample',episodes=result),indent=2,sort_keys=True)+'\n')
