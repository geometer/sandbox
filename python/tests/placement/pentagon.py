# https://www.facebook.com/groups/parmenides52/, problem 4580

import math

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestPentagon(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        scene.convex_polygon_constraint(A, B, C, D, E)
        A.segment(B).congruent_constraint(B.segment(C))
        A.segment(B).congruent_constraint(C.segment(D))
        A.segment(B).congruent_constraint(D.segment(E))
        A.segment(B).congruent_constraint(E.segment(A))
        A.segment(C).congruent_constraint(B.segment(D))
        A.segment(C).congruent_constraint(C.segment(E))
        A.segment(C).congruent_constraint(D.segment(A))
        A.segment(C).congruent_constraint(E.segment(B))

        return iterative_placement(scene)

    def testAngle(self):
        self.assertAngle('B', 'A', 'B', 'C', math.pi * 3 / 5)

    def testGoldenRatio(self):
        self.assertDistanceRatio('A', 'C', 'A', 'B', (1 + math.sqrt(5)) / 2)

class TestPentagonInCircle(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        circle = scene.free_point().circle_through(scene.free_point())
        A = circle.free_point(label='A')
        B = circle.free_point(label='B')
        C = circle.free_point(label='C')
        D = circle.free_point(label='D')
        E = circle.free_point(label='E')
        scene.convex_polygon_constraint(A, B, C, D, E)
        A.segment(B).congruent_constraint(B.segment(C))
        A.segment(B).congruent_constraint(C.segment(D))
        A.segment(B).congruent_constraint(D.segment(E))
        A.segment(B).congruent_constraint(E.segment(A))

        return iterative_placement(scene)

    def testAngle(self):
        self.assertAngle('B', 'A', 'B', 'C', math.pi * 3 / 5)

    def testGoldenRatio(self):
        self.assertDistanceRatio('A', 'C', 'A', 'B', (1 + math.sqrt(5)) / 2)
