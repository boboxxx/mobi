import hashlib,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('minimum_service_under_test',Path(__file__).resolve().parent/'minimal_registration.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class MinimalReceiverTests(unittest.TestCase):
    def setUp(self):
        p=dict(contract_sha256='ab'*32,registration=dict(catalog={'actor':[2,1,1]},calibration_sha256='cd'*32,calibration_receipt_sha256='ef'*32,model_freeze_sha256='01'*32,queries_um=[[-6000000,0],[6000000,0]],cap_us=500000,query_radius_um=750000,motion=dict(speed_um_s=5000000,acceleration_um_s2=3000000)));self.ctx=M.registration(p)
        self.obj=dict(version=1,kind='deadline',family='ridge',blueprint='actor',layout=0,frame=7,source_us=9876543,contract='ab'*32,calibration='cd'*32,status='bounded',lower_us=[123456,456789])
    def test_source_epoch_and_ages_preserved_without_threshold_tables(self):
        out=M.decode(M.compress(self.obj),'ridge',self.ctx);self.assertEqual(out['source_us'],9876543);self.assertEqual(out['lower_us'],[123456,456789]);self.assertNotIn('registry',self.ctx)
    def test_bad_identity_or_age_rejected(self):
        for field,value in [('family','joint'),('contract','00'*32),('calibration','00'*32),('lower_us',[-1,500001])]:
            obj=dict(self.obj);obj[field]=value
            with self.assertRaises(AssertionError):M.decode(M.compress(obj),'ridge',self.ctx)
    def test_minimum_setup_is_bound_to_approved_identity(self):
        wire=M.compress(self.ctx);h=hashlib.sha256(M.canon(self.ctx)).hexdigest();self.assertEqual(M.setup_decode(wire,h),self.ctx)
        with self.assertRaises(AssertionError):M.setup_decode(wire,'00'*32)
if __name__=='__main__':unittest.main()
