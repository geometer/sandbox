import sympy as sp

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestEquilateral(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.equal_distances_constraint((A, B), (A, C))
        altitude = C.perpendicular_line(A.line_through(B), label='CD')
        D = altitude.intersection_point(A.line_through(B, label='AB'))
        scene.distances_ratio_constraint((A, B), (C, D), sp.sqrt(3) / 2, 1)

        return iterative_placement(scene)

    def test_equilateral(self):
        self.assertEqualDistances('A', 'B', 'B', 'C')
