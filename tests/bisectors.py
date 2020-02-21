from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTriangleBisectors(PlacementTest):
    def setUp(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        bisectorA = scene.angle_bisector_line(A, B, C)
        bisectorB = scene.angle_bisector_line(B, A, C)
        bisectorC = scene.angle_bisector_line(C, A, B)
        X = bisectorA.intersection_point(bisectorB, label='X')
        Y = bisectorA.intersection_point(bisectorC, label='Y')

        self.placement = iterative_placement(scene)

    def test0(self):
        self.assertDistance('X', 'Y', 0)
