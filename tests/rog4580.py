# https://www.facebook.com/groups/parmenides52/, problem 4580

import math

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestRoG4580(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        scene.distances_ratio_constraint((A, B), (B, C), 2)
        scene.right_angle_constraint((A, B), (B, C))
        F = scene.incentre_point(A, B, C, label='F')
        E = scene.perpendicular_foot_point(B, A.line_through(F), label='E')

        return iterative_placement(scene)

    def testRightTriangle(self):
        self.assertAngle('B', 'A', 'B', 'C', math.pi / 2)

    def testGivenRatio(self):
        self.assertDistanceRatio('A', 'B', 'B', 'C', 2)

    def testGoldenRatio(self):
        self.assertDistanceRatio('B', 'E', 'E', 'F', (1 + math.sqrt(5)) / 2)
