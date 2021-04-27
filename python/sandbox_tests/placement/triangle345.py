from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTriangle345(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        A.distance_constraint('B', 5)
        C.distance_constraint('B', 4)
        C.distance_constraint('A', 3)
        scene.incircle(triangle, label='incircle')
        scene.circumcircle(triangle, label='circumcircle')

        return iterative_placement(scene)

    def test_ab(self):
        self.assertDistance('A', 'B', 5)

    def test_ac(self):
        self.assertDistance('A', 'C', 3)

    def test_bc(self):
        self.assertDistance('B', 'C', 4)

    def test_incircle(self):
        self.assertRadius('incircle', 1)

    def test_circumcircle(self):
        self.assertRadius('circumcircle', 2.5)
