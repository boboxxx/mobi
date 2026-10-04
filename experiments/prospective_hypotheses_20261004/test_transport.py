import hashlib,unittest
from fractions import Fraction as F
from transport import canon,compress,decode_setup,encode,decode
from inference import infer,compact
from produce import order,METHODS
class TransportTests(unittest.TestCase):
    def setUp(self):
        self.h=[[[0,0],[100,0],[100,100],[0,100]]];self.ext=[2.,1.,1.];self.row=dict(blueprint='actor',layout=0,frame=3,source_us=1234567)
        self.ctx=dict(version=1,catalog={'actor':self.ext},registry={'actor':{m:[1,1] for m in ('joint','ridge','local_mean','local_modes')}},calibration_sha256='ab'*32);self.contract=hashlib.sha256(canon(self.ctx)).hexdigest()
    def test_equal_inference_original_epoch(self):
        for family,hyp in [('joint',{}),('ridge',{'center_um':[1000000,1000000]}),('local_mean',{'status':'supported','mean_um':[1000000,1000000],'single_scale_um':50000}),('local_modes',{'status':'supported','centers_um':[[1000000,1000000],[1200000,1000000]],'modes_scale_um':50000})]:
            expected=compact(infer(self.h,self.ext,hyp,F(1),family))
            for kind in ('function','deadline'):
                packet=encode(self.row,family,kind,self.h,hyp,self.ctx,self.contract);out=decode(packet,family,kind,self.ctx,self.contract);self.assertEqual({k:out[k] for k in expected},expected);self.assertEqual(out['source_us'],1234567)
    def test_wrong_epoch_contract_and_family_rejected(self):
        packet=encode(self.row,'ridge','function',self.h,{'center_um':[0,0]},self.ctx,self.contract)
        with self.assertRaises(AssertionError):decode(packet,'ridge','function',self.ctx,'00'*32)
        with self.assertRaises(AssertionError):decode(packet,'joint','function',self.ctx,self.contract)
    def test_refusal_never_fabricates_deadline(self):
        for family,hyp in [('joint',{}),('ridge',{'center_um':None}),('local_mean',{'status':'refused'}),('local_modes',{'status':'refused'})]:
            for kind in ('function','deadline'):
                packet=encode(self.row,family,kind,[],hyp,self.ctx,self.contract);out=decode(packet,family,kind,self.ctx,self.contract);self.assertEqual((out['status'],out['lower_us']),('refused',[]))
    def test_shuffle_is_stable_and_complete(self):
        for iteration in range(3):self.assertEqual(set(order('row',iteration)),set(METHODS));self.assertEqual(order('row',iteration),order('row',iteration))
        self.assertNotEqual(order('row',0),order('row',1))
    def test_negative_deadline_and_corrupt_checksum_rejected(self):
        packet=encode(self.row,'ridge','deadline',self.h,{'center_um':[0,0]},self.ctx,self.contract)
        from transport import expand
        obj=expand(packet);obj['lower_us']=[-1,500001]
        with self.assertRaises(AssertionError):decode(compress(obj),'ridge','deadline',self.ctx,self.contract)
        bad=bytearray(packet);bad[-2]^=1
        with self.assertRaises(Exception):decode(bytes(bad),'ridge','deadline',self.ctx,self.contract)
if __name__=='__main__':unittest.main()
