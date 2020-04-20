from sandbox import Scene, iterative_placement

from .base import PlacementTest

class MorleyTrisectorsTest(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        A1 = scene.free_point(label='A1')
        B1 = scene.free_point(label='B1')
        C1 = scene.free_point(label='C1')
        angleA = A.angle(B, C)
        angleA.ratio_constraint(A.angle(B, C1), 3)
        angleA.ratio_constraint(A.angle(C1, B1), 3)
        angleA.ratio_constraint(A.angle(B1, C), 3)
        B1.inside_constraint(angleA)
        C1.inside_constraint(angleA)
        angleB = B.angle(A, C)
        angleB.ratio_constraint(B.angle(C, A1), 3)
        angleB.ratio_constraint(B.angle(A1, C1), 3)
        angleB.ratio_constraint(B.angle(C1, A), 3)
        A1.inside_constraint(angleB)
        C1.inside_constraint(angleB)
        angleC = C.angle(A, B)
        angleC.ratio_constraint(C.angle(A, B1), 3)
        angleC.ratio_constraint(C.angle(B1, A1), 3)
        angleC.ratio_constraint(C.angle(A1, B), 3)
        A1.inside_constraint(angleC)
        B1.inside_constraint(angleC)

        return iterative_placement(scene)

    def testEquilateral(self):
        self.assertEqualDistances('A1', 'B1', 'A1', 'C1')
        self.assertEqualDistances('A1', 'B1', 'B1', 'C1')
