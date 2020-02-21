# Problem 7 from http://zadachi.mccme.ru/2012/

import math

from sandbox import Scene, iterative_placement

from .base import SandboxTest

class TestMCCME7_long(SandboxTest):
    def setUp(self):
        scene = Scene()

        O = scene.free_point(label='O')
        circle = O.circle_through(scene.free_point(auxiliary=True))
        A = circle.free_point(label='A')
        B = circle.free_point(label='B')
        C = circle.free_point(label='C')
        D = circle.free_point(label='D')
        scene.quadrilateral_constraint(A, B, C, D)
        A.distance_constraint(B, 3)
        B.distance_constraint(C, 4)
        C.distance_constraint(D, 5)
        A.distance_constraint(D, 2)

        self.placement = iterative_placement(scene)

    def test1(self):
        self.assertDistance('A', 'C', math.sqrt(299.0 / 11))

class TestMCCME7_quick(SandboxTest):
    def setUp(self):
        scene = Scene()

        O = scene.free_point(label='O', x=0, y=0)
        A = scene.free_point(label='A')
        circle = O.circle_through(A)
        B = circle.free_point(label='B')
        C = circle.free_point(label='C')
        D = circle.free_point(label='D')
        scene.quadrilateral_constraint(A, B, C, D)
        A.distance_constraint(B, 3)
        B.distance_constraint(C, 4)
        C.distance_constraint(D, 5)
        A.distance_constraint(D, 2)

        self.placement = iterative_placement(scene)

    def test1(self):
        self.assertDistance('A', 'C', math.sqrt(299.0 / 11))
