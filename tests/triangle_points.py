from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTrianglePoints(PlacementTest):
    def setUp(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')

        bisectorA = scene.angle_bisector_line(A, B, C)
        bisectorB = scene.angle_bisector_line(B, A, C)
        bisectorC = scene.angle_bisector_line(C, A, B)
        X_bisector = bisectorA.intersection_point(bisectorB, label='X_bisector')
        Y_bisector = bisectorA.intersection_point(bisectorC, label='Y_bisector')

        heightA = A.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        heightB = B.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        heightC = C.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        X_height = heightA.intersection_point(heightB, label='X_height')
        Y_height = heightA.intersection_point(heightC, label='Y_height')

        perpA = scene.perpendicular_bisector_line(B, C)
        perpB = scene.perpendicular_bisector_line(A, C)
        perpC = scene.perpendicular_bisector_line(A, B)
        X_perp = perpA.intersection_point(perpB, label='X_perp')
        Y_perp = perpA.intersection_point(perpC, label='Y_perp')

        medianA = A.line_through(B.ratio_point(C, 1, 1))
        medianB = B.line_through(A.ratio_point(C, 1, 1))
        medianC = C.line_through(A.ratio_point(B, 1, 1))
        X_median = medianA.intersection_point(medianB, label='X_median')
        Y_median = medianA.intersection_point(medianC, label='Y_median')

        self.placement = iterative_placement(scene)

    def testBisectors(self):
        self.assertDistance('X_bisector', 'Y_bisector', 0)

    def testHeights(self):
        self.assertDistance('X_height', 'Y_height', 0)

    def testPerpendicularBisectors(self):
        self.assertDistance('X_perp', 'Y_perp', 0)

    def testMedians(self):
        self.assertDistance('X_median', 'Y_median', 0)
