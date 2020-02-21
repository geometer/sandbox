import unittest
import mpmath

from sandbox import Scene, iterative_placement

class TestTriangle345(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        A.distance_constraint('B', 5)
        C.distance_constraint('B', 4)
        C.distance_constraint('A', 3)

        self.placement = iterative_placement(scene)

    def test_ab(self):
        assert mpmath.fabs(self.placement.distance('A', 'B') - 5) < 1e-6, '|AB| != 5'

    def test_ac(self):
        assert mpmath.fabs(self.placement.distance('A', 'C') - 3) < 1e-6, '|AC| != 3'

    def test_bc(self):
        assert mpmath.fabs(self.placement.distance('B', 'C') - 4) < 1e-6, '|BC| != 4'
