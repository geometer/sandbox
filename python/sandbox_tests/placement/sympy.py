import sympy as sp

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestSympy1(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        A.segment(B).congruent_constraint(A.segment(C))
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'))
        B.segment(C).ratio_constraint(A.segment(D), 2 / sp.sqrt(3))

        return iterative_placement(scene)

    def test_equilateral(self):
        self.assertEqualDistances('A', 'B', 'B', 'C')

class TestSympy2(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        A.segment(B).congruent_constraint(A.segment(C))
        A.segment(B).congruent_constraint(B.segment(C))
        A.segment(B).length_constraint(1)
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'), label='D')

        return iterative_placement(scene)

    def test_altitude(self):
        self.assertDistance('A', 'D', sp.sqrt(3) / 2)

class TestSympy3(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        A.segment(B).congruent_constraint(A.segment(C))
        A.segment(B).congruent_constraint(B.segment(C))
        A.segment(B).length_constraint(sp.sqrt(3))
        altitude = A.perpendicular_line(B.line_through(C), label='AD')
        D = altitude.intersection_point(B.line_through(C, label='BC'), label='D')

        return iterative_placement(scene)

    def test_altitude(self):
        self.assertDistance('A', 'D', sp.sympify(3) / 2)
