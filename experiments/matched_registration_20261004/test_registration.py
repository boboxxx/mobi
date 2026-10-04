import hashlib,unittest
from common import parent,lease,decode,decode_setup,encode_setup,canon
class RegistrationTests(unittest.TestCase):
 def ctx(self):return dict(primary_context_sha256='11'*32,calibration_sha256='22'*32,catalog={'known':[.5,.4,.2]},registry={'known':{'joint_slack_um':0}})
 def test_same_membership_with_lighter_context(self):
  c=self.ctx();h=[[[-10,-10],[10,-10],[10,10],[-10,10]]];expected=parent.infer(h,c['catalog']['known'],0,'joint_hull');w=parent.pack(h,0,0,17,125000,c['primary_context_sha256'],c['calibration_sha256']);a=decode(w,'hull',c);b=decode(lease.encode(expected,0,0,17,125000,c['primary_context_sha256'],c['calibration_sha256']),'deadline',c);self.assertEqual((a['status'],a['lower_us'],a['source_us']),(b['status'],b['lower_us'],125000))
 def test_source_epoch_and_refusal_preserved(self):
  c=self.ctx();w=parent.pack([],0,1,18,250000,c['primary_context_sha256'],c['calibration_sha256']);a=decode(w,'hull',c);self.assertEqual((a['status'],a['lower_us'],a['source_us']),('refused',[],250000));c=dict(c,calibration_sha256='33'*32)
  with self.assertRaises(AssertionError):decode(w,'hull',c)
 def test_setup_hash_corruption_rejected(self):
  w=encode_setup(dict(registry={},queries_um=[]))
  with self.assertRaises(AssertionError):decode_setup(w,'00'*32)
if __name__=='__main__':unittest.main()
