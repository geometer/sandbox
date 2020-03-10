from sandbox import Scene, iterative_placement

from .base import PlacementTest

class TestTrianglePoints(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))

        bisectorA = scene.angle_bisector_line(A.angle(B, C))
        bisectorB = scene.angle_bisector_line(B.angle(A, C))
        bisectorC = scene.angle_bisector_line(C.angle(A, B))
        X_bisector = bisectorA.intersection_point(bisectorB, label='X_bisector')
        Y_bisector = bisectorA.intersection_point(bisectorC, label='Y_bisector')

        altitudeA = A.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        altitudeB = B.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        altitudeC = C.line_through(scene.perpendicular_foot_point(A, B.line_through(C)))
        X_altitude = altitudeA.intersection_point(altitudeB, label='X_altitude')
        Y_altitude = altitudeA.intersection_point(altitudeC, label='Y_altitude')

        perpA = scene.perpendicular_bisector_line(B, C)
        perpB = scene.perpendicular_bisector_line(A, C)
        perpC = scene.perpendicular_bisector_line(A, B)
        X_perp = perpA.intersection_point(perpB, label='X_perp')
        Y_perp = perpA.intersection_point(perpC, label='Y_perp')

        medianA = A.line_through(scene.middle_point(B, C))
        medianB = B.line_through(scene.middle_point(A, C))
        medianC = C.line_through(scene.middle_point(A, B))
        X_median = medianA.intersection_point(medianB, label='X_median')
        Y_median = medianA.intersection_point(medianC, label='Y_median')

        return iterative_placement(scene)

    def testBisectors(self):
        self.assertDistance('X_bisector', 'Y_bisector', 0)

    def testHeights(self):
        self.assertDistance('X_altitude', 'Y_altitude', 0)

    def testPerpendicularBisectors(self):
        self.assertDistance('X_perp', 'Y_perp', 0)

    def testMedians(self):
        self.assertDistance('X_median', 'Y_median', 0)

class TestCircumcentre(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        O = scene.circumcentre_point((A, B, C), label='O')

        return iterative_placement(scene)

    def testOAOB(self):
        self.assertEqualDistances('O', 'A', 'O', 'B')

    def testOAOC(self):
        self.assertEqualDistances('O', 'A', 'O', 'C')

    def testOBOC(self):
        self.assertEqualDistances('O', 'B', 'O', 'C')
