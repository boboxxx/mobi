import gzip,importlib.util,json,sys,unittest
from pathlib import Path
from fractions import Fraction as F
import numpy as np
E=Path(__file__).resolve().parent;ROOT=E.parents[1]
spec=importlib.util.spec_from_file_location('test_fixed_episode_runtime',E/'runtime.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
spec=importlib.util.spec_from_file_location('test_fixed_episode_stats',E/'certify.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
P=ROOT/'results/near_expiry_live_20261004/capture'
class ProtocolTests(unittest.TestCase):
 def test_single_serialization_and_label_blind_sources(self):
  ctx=json.loads((P/'context.json').read_bytes());models=R.load_models();background=json.loads((ROOT/'results/background_frontend_20261004/background.json').read_bytes());outcomes=json.loads((P/'outcomes.json').read_bytes())
  for bp in ('vehicle.audi.a2','vehicle.diamondback.century','walker.pedestrian.0001'):
   o=next(o for o in outcomes if o['request']['blueprint']==bp and o['request']['method']=='function' and o['request']['start_x_m']==8*-1);d=json.loads(gzip.decompress((P/o['file']).read_bytes()));s=d['sources'][0]
   with np.load(P/'clouds'/s['cloud']) as z:raw=z['raw'].copy();T=z['transform'].copy()
   base,meta=R.BASE.encode(raw,T,s['own'],d['body'],ctx,bp,'function',s['source_us'],s['frame'],models,background)
   for method in ('function','deadline','cone'):
    counter=[];old=R.pack
    def counted(obj):counter.append(1);return old(obj)
    R.pack=counted
    try:wire,got=R.encode(raw,T,s['own'],d['body'],ctx,bp,method,s['source_us'],s['frame'],models,background)
    finally:R.pack=old
    self.assertEqual(counter,[1]);decoded=R.decode(wire,ctx);self.assertEqual(decoded['obj']['source_us'],s['source_us'])
    if method=='function':self.assertEqual(wire,base);self.assertEqual(got,meta)
    elif method=='deadline':self.assertEqual(decoded['obj']['proposal']['proposal_valid_until_us'],s['source_us']+got['source_proposal']['lower_us'])
    else:
     proposal,gate=R.choose(decoded,s['own'],d['body'],ctx,s['source_us']);direct=R.evidence(got['original'],ctx).query(R.query_position(s['own'],ctx['basis']),R.action_radius(d['body']));self.assertEqual(proposal['distance_lower_um'],direct['distance_lower_um']);self.assertEqual(proposal['lower_us'],direct['lower_us']);self.assertTrue(gate['query_domain_valid'])
     moved=dict(s['own']);moved['center']=(np.asarray(s['own']['center'])+np.asarray(ctx['basis']['road'])@np.array([.2,.1,0.])).tolist();shifted,shift_gate=R.choose(decoded,moved,d['body'],ctx,s['source_us']+12345);self.assertEqual(shifted['source_us'],s['source_us']);self.assertEqual(shifted['proposal_valid_until_us'],s['source_us']+shifted['lower_us']);self.assertLessEqual(shifted['distance_lower_um'],direct['distance_lower_um']);self.assertTrue(shift_gate['query_domain_valid'])
    mutated=raw.copy();mutated['id']=np.arange(len(raw),dtype='<u4');mutated['tag']=4294967295
    again,again_meta=R.encode(mutated,T,s['own'],d['body'],ctx,bp,method,s['source_us'],s['frame'],models,background);self.assertEqual(again,wire);self.assertEqual(again_meta,got)
 def test_selection_can_destroy_marginal_risk(self):
  selected=[True]*5+[False]*95;failed=[True]*5+[False]*95
  c=C.stats.certificate(selected,failed,risk=F(1,20),delta=F(1,20),policies=3)
  self.assertFalse(c['accepted']);self.assertEqual(c['conditional_upper'],[1,1])
 def test_complete_episode_unit_and_zero_failure_boundary(self):
  self.assertEqual(C.stats.zero_failure_required(F(1,20),F(1,20),3),80)
  for n,expected in [(0,False),(79,False),(80,True)]:
   c=C.stats.certificate([True]*n,[False]*n,risk=F(1,20),delta=F(1,20),policies=3);self.assertEqual(c['accepted'],expected)
if __name__=='__main__':unittest.main()
