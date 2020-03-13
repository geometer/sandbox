from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTrisectors(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        A1 = scene.free_point(label='A1')
        B1 = scene.free_point(label='B1')
        C1 = scene.free_point(label='C1')
        A.angle(B, C).ratio_constraint(A.angle(B, C1), 3)
        A.angle(B, C).ratio_constraint(A.angle(B1, C), 3)
        B.angle(C, A).ratio_constraint(B.angle(C, A1), 3)
        B.angle(C, A).ratio_constraint(B.angle(C1, A), 3)
        C.angle(A, B).ratio_constraint(C.angle(A, B1), 3)
        C.angle(A, B).ratio_constraint(C.angle(A1, B), 3)

        return iterative_placement(scene)

    def testEquilateral(self):
        self.assertEqualDistances('A1', 'B1', 'A1', 'C1')
        self.assertEqualDistances('A1', 'B1', 'B1', 'C1')
