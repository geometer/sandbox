# https://www.facebook.com/groups/parmenides52/, problem 4578

import math

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestRoG4578_orthocenter_inside(PlacementTest):
    def setUp(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        A1 = scene.perpendicular_foot_point(A, B.line_through(C), label='A1')
        B1 = scene.perpendicular_foot_point(B, C.line_through(A), label='B1')
        D = A.line_through(A1).intersection_point(B.line_through(B1), label='D')
        D.inside_triangle_constraint(A, B, C)
        scene.equal_distances_constraint((A, B), (C, D))

        self.placement = iterative_placement(scene)

    def testACB(self):
        self.assertAngle('C', 'A', 'C', 'B', math.pi / 4)

class TestRoG4578_orthocenter_outside(PlacementTest):
    def setUp(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        A1 = scene.perpendicular_foot_point(A, B.line_through(C), label='A1')
        B1 = scene.perpendicular_foot_point(B, C.line_through(A), label='B1')
        D = A.line_through(A1).intersection_point(B.line_through(B1), label='D')
        D.opposite_side_constraint(B.line_through(C), A)
        D.opposite_side_constraint(A.line_through(C), B)
        scene.equal_distances_constraint((A, B), (C, D))

        self.placement = iterative_placement(scene)

    def testACB(self):
        self.assertAngle('C', 'A', 'C', 'B', 3 * math.pi / 4)
