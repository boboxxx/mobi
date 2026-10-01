import unittest
import numpy as np
from audit_geometry import rotation,vertices


class GeometryTests(unittest.TestCase):
    def test_coordinate_axes_and_composition(self):
        np.testing.assert_allclose(rotation(0,90,0)@np.array([1.,0,0]),[0,1,0],atol=1e-12)
        np.testing.assert_allclose(rotation(90,0,0)@np.array([1.,0,0]),[0,0,1],atol=1e-12)
        np.testing.assert_allclose(rotation(0,0,90)@np.array([0.,1,0]),[0,0,-1],atol=1e-12)
        r=rotation(12,45,-8);np.testing.assert_allclose(r@r.T,np.eye(3),atol=1e-12)

    def test_local_box_offset_before_vehicle_rotation(self):
        box=dict(half_length=2.,half_width=1.,half_height=.5,offset_x=.1,offset_y=0.,offset_z=.2,rotation=dict(pitch=0.,yaw=0.,roll=0.));state=dict(x=10.,y=20.,z=0.,pitch=0.,yaw=90.,roll=0.)
        np.testing.assert_allclose(vertices(box,state)[0],[11.,18.1,-.3],atol=1e-12)


if __name__=='__main__':unittest.main()
