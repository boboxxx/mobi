import unittest
from fractions import Fraction as F
from geometry import infer,conformity,error_um
from model import predict,fit,prepare

class Geometry(unittest.TestCase):
    def test_geometry_prunes_incompatible_near_query_mode(self):
        h=[[[0,0]],[[600,0]]];ext=[.5,.2,.2];p=dict(status='supported',mean_um=[0,0],centers_um=[[0,0],[7000000,0]],single_scale_um=100000,modes_scale_um=100000)
        a=infer(h,ext,p,F(1),'local_modes','plain');b=infer(h,ext,p,F(1),'local_modes','max');c=infer(h,ext,p,F(1),'local_modes','clip')
        self.assertEqual(a['lower_us'][1],0);self.assertGreater(c['lower_us'][1],b['lower_us'][1]);self.assertGreater(c['pruned_pairs'],0)
    def test_contradiction_refuses_and_fallback_keeps_geometry(self):
        h=[[[0,0]]];ext=[.5,.2,.2];p=dict(status='supported',mean_um=[6000000,0],centers_um=[[6000000,0]],single_scale_um=100000,modes_scale_um=100000)
        self.assertEqual(infer(h,ext,p,F(1),'local_mean')['status'],'empty')
        p['status']='fallback';self.assertEqual(infer(h,ext,p,F(1),'local_mean')['status'],'bounded')
        self.assertEqual(infer([],ext,p,F(1),'local_mean')['status'],'refused')
    def test_direct_membership_score_and_outward_radius(self):
        h=[[[0,0]]];ext=[.5,.2,.2];p=dict(status='supported',mean_um=[0,0],centers_um=[[0,0]],single_scale_um=100000,modes_scale_um=100000);xy=[.10000000001,0]
        q=conformity(h,ext,p,xy,'local_mean');g=infer(h,ext,p,q,'local_mean');self.assertEqual(g['radius_um'],error_um([0,0],xy));self.assertEqual(g['status'],'bounded')
    def test_episode_exclusion_and_unsupported_range(self):
        rows=[];labels={}
        for i in range(12):
            r=dict(id=str(i),episode_id=str(i),layout=0,hulls_cm=[[[0,0],[100+i,0],[0,100]]]);rows.append(r);labels[str(i)]=[.5,.5]
        m=fit(rows,labels);self.assertEqual(m['training_rows'],12);p=predict([[[0,0],[100000,0],[0,100000]]],0,m,prepare(m));self.assertEqual(p['status'],'fallback')
if __name__=='__main__':unittest.main()
