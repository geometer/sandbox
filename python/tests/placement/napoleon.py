import math

from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestNapoleon(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')

        def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
            c0 = A.circle_through(B)
            c1 = B.circle_through(A)
            line = A.line_through(B, layer='auxiliary')
            V = c0.intersection_point(c1, label=C.label + '1')
            V.opposite_side_constraint(C, line)
            scene.centroid_point((A, B, V), label=C.label + '2')

        napoleonic(A, B, C)
        napoleonic(C, A, B)
        napoleonic(B, C, A)

        return iterative_placement(scene)

    def test1(self):
        self.assertEqualDistances('A2', 'B2', 'A2', 'C2')

    def test2(self):
        self.assertEqualDistances('A2', 'B2', 'B2', 'C2')

    def test3(self):
        self.assertDistanceRatio('A', 'A1', 'A2', 'B2', math.sqrt(3))

    def test4(self):
        self.assertDistanceRatio('C', 'A', 'C', 'B2', math.sqrt(3))

    def test5(self):
        self.assertDistanceRatio('C', 'A1', 'C', 'A2', math.sqrt(3))

    def test6(self):
        self.assertAngle('A', 'A1', 'B2', 'A2', math.pi / 6)

    def test7(self):
        self.assertEqualSignedAngles('C', 'A', 'C', 'A1', 'C', 'B2', 'C', 'A2')
