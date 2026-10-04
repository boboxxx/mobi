import unittest
from integer_state import age,circle_age,error_um,oracle_age
from predictor import predict

class Bounds(unittest.TestCase):
    def test_strict_contact_and_age(self):
        self.assertEqual(age(0),0)
        t=age(1000000)
        self.assertLess(2*5000000*t*1000000+3000000*t*t,2*1000000*1000000000000)
        self.assertGreaterEqual(2*5000000*(t+1)*1000000+3000000*(t+1)**2,2*1000000*1000000000000)
        self.assertEqual(age(1000000000),500000)
    def test_calibrated_radius_prevents_query_overstatement(self):
        for xy in ([.1000000001,-.2000000002],[-5.50000000001,0.]):
            centre=[100000,-200000];rad=error_um(centre,xy)
            for q in ([-6000000,0],[6000000,0],[20000,35000]):
                self.assertLessEqual(circle_age(centre,rad,700000,q),oracle_age(xy,700000,q))
    def test_empty_refusal_and_hull_only_api(self):
        self.assertIsNone(predict([],0,{'method':'bbox'}))
        self.assertEqual(predict([[[0,0],[200,0],[0,200]]],0,{'method':'bbox'}),[1000000,1000000])
if __name__=='__main__':unittest.main()
