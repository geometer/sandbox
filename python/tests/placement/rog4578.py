# https://www.facebook.com/groups/parmenides52/, problem 4578

import math

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestRoG4578_orthocentre_inside(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        D = scene.orthocentre_point(triangle)
        D.inside_triangle_constraint(triangle)
        A.segment(B).congruent_constraint(C.segment(D))

        return iterative_placement(scene)

    def testACB(self):
        self.assertAngle('C', 'A', 'C', 'B', math.pi / 4)

class TestRoG4578_orthocentre_outside(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        D = scene.orthocentre_point(triangle)
        D.opposite_side_constraint(B.line_through(C), A)
        D.opposite_side_constraint(A.line_through(C), B)
        A.segment(B).congruent_constraint(C.segment(D))

        return iterative_placement(scene)

    def testACB(self):
        self.assertAngle('C', 'A', 'C', 'B', 3 * math.pi / 4)
