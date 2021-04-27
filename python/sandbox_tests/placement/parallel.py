from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestParallel(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        A.distance_constraint(B, 5)
        C.distance_constraint(B, 3)
        C.distance_constraint(A, 4)
        D = scene.free_point(label='D')
        A.vector(D).parallel_constraint(C.vector(B))
        B.vector(D).parallel_constraint(C.vector(A))

        return iterative_placement(scene)

    def test_ad(self):
        self.assertDistance('A', 'D', 3)

    def test_bd(self):
        self.assertDistance('B', 'D', 4)

    def test_cd(self):
        self.assertDistance('C', 'D', 5)
