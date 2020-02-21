from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTriangle345(PlacementTest):
    def setUp(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        A.distance_constraint('B', 5)
        C.distance_constraint('B', 4)
        C.distance_constraint('A', 3)
        circle = scene.incircle(A, B, C, label='incircle')

        self.placement = iterative_placement(scene)

    def test_ab(self):
        self.assertDistance('A', 'B', 5)

    def test_ac(self):
        self.assertDistance('A', 'C', 3)

    def test_bc(self):
        self.assertDistance('B', 'C', 4)

    def test_incircle(self):
        self.assertRadius('incircle', 1)
