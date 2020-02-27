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
        scene.equal_distances_constraint((A, B), (B, C))
        scene.equal_distances_constraint((A, B), (C, D))
        scene.equal_distances_constraint((A, B), (D, E))
        scene.equal_distances_constraint((A, B), (E, A))
        scene.equal_distances_constraint((A, C), (B, D))
        scene.equal_distances_constraint((A, C), (C, E))
        scene.equal_distances_constraint((A, C), (D, A))
        scene.equal_distances_constraint((A, C), (E, B))

        return iterative_placement(scene)

    def testAngle(self):
        self.assertAngle('B', 'A', 'B', 'C', math.pi * 3 / 5)

    def testGoldenRatio(self):
        self.assertDistanceRatio('A', 'C', 'A', 'B', (1 + math.sqrt(5)) / 2)
