import time
import unittest
import mpmath

class PlacementTest(unittest.TestCase):
    ERROR = 1e-6

    def setUp(self):
        self.startTime = time.time()
        self.placement = self.createPlacement()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))

    def assertCoordinates(self, pt, x, y):
        loc = self.placement.location(pt)
        self.assertLess(
            mpmath.fabs(loc.x - x) + mpmath.fabs(loc.y - y),
            PlacementTest.ERROR,
            '%s != (%s,%s)' % (loc, x, y)
        )

    def assertDistance(self, pt0, pt1, distance):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - distance),
            PlacementTest.ERROR,
            '|%s,%s| != %d' % (pt0, pt1, distance)
        )

    def assertEqualDistances(self, pt0, pt1, pt2, pt3):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - self.placement.distance(pt2, pt3)),
            PlacementTest.ERROR,
            '|%s,%s| != |%s,%s|' % (pt0, pt1, pt2, pt3)
        )

    def assertDistanceRatio(self, pt0, pt1, pt2, pt3, ratio):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - self.placement.distance(pt2, pt3) * ratio),
            PlacementTest.ERROR,
            '|%s,%s| != |%s,%s| * %s' % (pt0, pt1, pt2, pt3, ratio)
        )

    def assertAngle(self, pt0, pt1, pt2, pt3, value):
        self.assertLess(
            mpmath.fabs(mpmath.fabs(self.placement.angle(pt0, pt1, pt2, pt3)) - value),
            PlacementTest.ERROR,
            '∠(%s,%s),(%s,%s) != %s' % (pt0, pt1, pt2, pt3, value)
        )

    def assertEqualSignedAngles(self, pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7):
        self.assertLess(
            mpmath.fabs(self.placement.angle(pt0, pt1, pt2, pt3) - self.placement.angle(pt4, pt5, pt6, pt7)),
            PlacementTest.ERROR,
            '∠(%s,%s),(%s,%s) != ∠(%s,%s),(%s,%s)' % (pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7)
        )

    def assertRadius(self, circle, radius):
        self.assertLess(
            mpmath.fabs(self.placement.radius(circle) - radius),
            PlacementTest.ERROR,
            'radius(%s) != %s' % (circle, radius)
        )
