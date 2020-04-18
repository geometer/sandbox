import time
import unittest
import numpy as np

from sandbox.core import CoreScene

class PlacementTest(unittest.TestCase):
    ERROR = np.float128(1e-5)

    def setUp(self):
        self.startTime = time.time()
        self.placement = self.createPlacement()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))

    def distance(self, point0, point1):
        if isinstance(point0, str):
            point0 = self.placement.scene.get(point0)
        if isinstance(point1, str):
            point1 = self.placement.scene.get(point1)

        assert isinstance(point0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(point1, CoreScene.Point), 'Parameter is not a point'

        if point0 == point1:
            return 0
        return self.placement.length(point0.vector(point1))

    def angle(self, pt0, pt1, pt2, pt3):
        """Angle between vectors (pt0, pt1) and (pt2, pt3)"""
        if isinstance(pt0, str):
            pt0 = self.placement.scene.get(pt0)
        if isinstance(pt1, str):
            pt1 = self.placement.scene.get(pt1)
        if isinstance(pt2, str):
            pt2 = self.placement.scene.get(pt2)
        if isinstance(pt3, str):
            pt3 = self.placement.scene.get(pt3)

        assert isinstance(pt0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt1, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt2, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt3, CoreScene.Point), 'Parameter is not a point'

        return self.placement.angle(pt0.vector(pt1).angle(pt2.vector(pt3)))

    def assertCoordinates(self, pt, x, y):
        loc = self.placement.location(pt)
        self.assertLess(
            np.fabs(loc.x - x) + np.fabs(loc.y - y),
            PlacementTest.ERROR,
            '%s != (%s,%s)' % (loc, x, y)
        )

    def assertDistance(self, pt0, pt1, distance):
        self.assertLess(
            np.fabs(self.distance(pt0, pt1) - np.float128(distance)),
            PlacementTest.ERROR,
            '|%s,%s| != %d' % (pt0, pt1, distance)
        )

    def assertEqualDistances(self, pt0, pt1, pt2, pt3):
        self.assertLess(
            np.fabs(self.distance(pt0, pt1) / self.distance(pt2, pt3) - 1),
            PlacementTest.ERROR,
            '|%s,%s| != |%s,%s|' % (pt0, pt1, pt2, pt3)
        )

    def assertDistanceRatio(self, pt0, pt1, pt2, pt3, ratio):
        self.assertLess(
            np.fabs(self.distance(pt0, pt1) / self.distance(pt2, pt3) - ratio),
            PlacementTest.ERROR,
            '|%s,%s| != |%s,%s| * %s' % (pt0, pt1, pt2, pt3, ratio)
        )

    def assertAngle(self, pt0, pt1, pt2, pt3, value):
        self.assertLess(
            np.fabs(np.fabs(self.angle(pt0, pt1, pt2, pt3)) - value),
            PlacementTest.ERROR,
            '∠(%s,%s),(%s,%s) != %s' % (pt0, pt1, pt2, pt3, value)
        )

    def assertEqualSignedAngles(self, pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7):
        self.assertLess(
            np.fabs(self.angle(pt0, pt1, pt2, pt3) - self.angle(pt4, pt5, pt6, pt7)),
            PlacementTest.ERROR,
            '∠(%s,%s),(%s,%s) != ∠(%s,%s),(%s,%s)' % (pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7)
        )

    def assertRadius(self, circle, radius):
        self.assertLess(
            np.fabs(self.placement.radius(circle) - radius),
            PlacementTest.ERROR,
            'radius(%s) != %s' % (circle, radius)
        )
