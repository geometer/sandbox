import unittest
import mpmath

class PlacementTest(unittest.TestCase):
    def assertCoordinates(self, pt, x, y):
        loc = self.placement.location(pt)
        self.assertLess(
            mpmath.fabs(loc.x - x) + mpmath.fabs(loc.y - y),
            1e-6,
            '%s != (%s,%s)' % (loc, x, y)
        )

    def assertDistance(self, pt0, pt1, distance):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - distance),
            1e-6,
            '|%s,%s| != %d' % (pt0, pt1, distance)
        )

    def assertEqualDistances(self, pt0, pt1, pt2, pt3):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - self.placement.distance(pt2, pt3)),
            1e-6,
            '|%s,%s| != |%s,%s|' % (pt0, pt1, pt2, pt3)
        )

    def assertDistanceRatio(self, pt0, pt1, pt2, pt3, ratio):
        self.assertLess(
            mpmath.fabs(self.placement.distance(pt0, pt1) - self.placement.distance(pt2, pt3) * ratio),
            1e-6,
            '|%s,%s| != |%s,%s| * %s' % (pt0, pt1, pt2, pt3, ratio)
        )

    def assertAngle(self, pt0, pt1, pt2, pt3, value):
        self.assertLess(
            mpmath.fabs(mpmath.fabs(self.placement.angle(pt0, pt1, pt2, pt3)) - value),
            1e-6,
            '∠(%s,%s),(%s,%s) != %s' % (pt0, pt1, pt2, pt3, value)
        )

    def assertEqualSignedAngles(self, pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7):
        self.assertLess(
            mpmath.fabs(self.placement.angle(pt0, pt1, pt2, pt3) - self.placement.angle(pt4, pt5, pt6, pt7)),
            1e-6,
            '∠(%s,%s),(%s,%s) != ∠(%s,%s),(%s,%s)' % (pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7)
        )

    def assertRadius(self, circle, radius):
        self.assertLess(
            mpmath.fabs(self.placement.radius(circle) - radius),
            1e-6,
            'radius(%s) != %s' % (circle, radius)
        )
