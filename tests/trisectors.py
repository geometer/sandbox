from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTrisectors(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        A1 = scene.free_point(label='A1')
        B1 = scene.free_point(label='B1')
        C1 = scene.free_point(label='C1')
        scene.angles_ratio_constraint(((B, C), (B, A)), ((B, C), (B, A1)), 3)
        scene.angles_ratio_constraint(((C, A), (C, B)), ((C, A1), (C, B)), 3)
        scene.angles_ratio_constraint(((C, A), (C, B)), ((C, A), (C, B1)), 3)
        scene.angles_ratio_constraint(((A, B), (A, C)), ((A, B1), (A, C)), 3)
        scene.angles_ratio_constraint(((A, B), (A, C)), ((A, B), (A, C1)), 3)
        scene.angles_ratio_constraint(((B, C), (B, A)), ((B, C1), (B, A)), 3)

        return iterative_placement(scene)

    def testEquilateral(self):
        self.assertEqualDistances('A1', 'B1', 'A1', 'C1')
        self.assertEqualDistances('A1', 'B1', 'B1', 'C1')
