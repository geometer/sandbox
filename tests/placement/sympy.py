import sympy as sp

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestSympy1(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.equal_distances_constraint((A, B), (A, C))
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'))
        scene.distances_ratio_constraint((B, C), (A, D), sp.sqrt(3) / 2, 1)

        return iterative_placement(scene)

    def test_equilateral(self):
        self.assertEqualDistances('A', 'B', 'B', 'C')

class TestSympy2(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.equal_distances_constraint((A, B), (A, C))
        scene.equal_distances_constraint((A, B), (B, C))
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'), label='D')
        A.distance_constraint(B, 1)

        return iterative_placement(scene)

    def test_altitude(self):
        self.assertDistance('A', 'D', sp.sqrt(3) / 2)

class TestSympy3(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.equal_distances_constraint((A, B), (A, C))
        scene.equal_distances_constraint((A, B), (B, C))
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'), label='D')
        A.distance_constraint(B, sp.sqrt(3))

        return iterative_placement(scene)

    def test_altitude(self):
        self.assertDistance('A', 'D', sp.sympify(3) / 2)
