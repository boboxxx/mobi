import unittest
from lease_baseline import encode,decode
class LeaseTests(unittest.TestCase):
 def test_source_epoch_and_refusal_are_preserved(self):
  h='12'*32;c='34'*32;cat={'known':[1,1,1]}
  for status,ages in [('bounded',[100,499999]),('refused',[]),('empty',[])]:
   out=decode(encode(dict(status=status,lower_us=ages),0,1,15,43000,h,c),h,c,cat);self.assertEqual(out,dict(status=status,lower_us=ages,class_index=0,layout=1,frame=15,source_us=43000))
 def test_wrong_context_checksum_and_excessive_horizon_fail(self):
  h='12'*32;c='34'*32;cat={'known':[1,1,1]};w=encode(dict(status='bounded',lower_us=[10,20]),0,1,15,43000,h,c)
  with self.assertRaises(AssertionError):decode(w,'56'*32,c,cat)
  bad=bytearray(w);bad[-4]^=1
  with self.assertRaises(Exception):decode(bytes(bad),h,c,cat)
  w=encode(dict(status='bounded',lower_us=[10,500001]),0,1,15,43000,h,c)
  with self.assertRaises(AssertionError):decode(w,h,c,cat)
if __name__=='__main__':unittest.main()
