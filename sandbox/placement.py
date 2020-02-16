import math
import random
from typing import List, Set

from .objects import Scene
from .objects import Point, FreePoint, FreePointOnLine, FreePointOnCircle, CentrePoint, CirclesIntersection

class TwoDCoordinates:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return '(%.5f, %.5f)' % (self.x, self.y)

    def __eq__(self, other):
        return math.fabs(self.x - other.x) < 5e-6 and math.fabs(self.y - other.y) < 5e-6

    def distanceTo(self, other) -> float:
        return TwoDVector(other, self).length

    def distance2To(self, other) -> float:
        return TwoDVector(other, self).length2

class TwoDVector:
    def __init__(self, start: TwoDCoordinates, end: TwoDCoordinates):
        self.x = end.x - start.x
        self.y = end.y - start.y

    @property
    def length(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def length2(self) -> float:
        return self.x * self.x + self.y * self.y

    def scalar_product(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def vector_product(self, other) -> float:
        return self.x * other.y - self.y * other.x

    def angle(self, other) -> float:
        cos = self.scalar_product(other) / self.length / other.length
        if cos >= 1:
            return 0
        elif cos <= -1:
            return math.pi if self.vector_product(other) > 0 else -math.pi
        else:
            return math.acos(cos) if self.vector_product(other) > 0 else -math.acos(cos)

class IncompletePlacementError(Exception):
    """Internal error, should never be thrown to public"""

class PlacementFailedError(Exception):
    """Cannot place to meet all the conditions"""

class Placement:
    class TempPlacement:
        def __init__(self, placement, point, coords):
            self._coordinates = dict(placement._coordinates)
            self._coordinates[point] = coords

        def location(self, point: Point) -> TwoDCoordinates:
            loca = self._coordinates.get(point)
            if loca is None:
                raise IncompletePlacementError
            return loca

    def __init__(self, scene: Scene):
        self.scene = scene
        self._coordinates = {}
        not_placed: Set[Point] = set(scene.points)

        def add(p: Point, coords):
            if isinstance(coords, TwoDCoordinates):
                coords = [coords]
            for candidate in coords:
                temp = Placement.TempPlacement(self, p, candidate)
                if all(cs.validate(temp) for cs in p.constraints):
                    self._coordinates[p] = candidate
                    not_placed.remove(p)
                    return
            raise PlacementFailedError

        while len(not_placed) > 0:
            for p in list(not_placed):
                try:
                    if isinstance(p, FreePoint):
                        add(p, TwoDCoordinates(
                            p.x if hasattr(p, 'x') else random.randrange(0, 100000, 1) / 1000.0,
                            p.y if hasattr(p, 'y') else random.randrange(0, 100000, 1) / 1000.0
                        ))
                    elif isinstance(p, FreePointOnCircle):
                        o = self.location(p.circle.centre)
                        r = o.distanceTo(self.location(p.circle.point))
                        angle = random.randrange(0, 200000, 1) * math.pi / 100000
                        add(p, TwoDCoordinates(
                            o.x + math.sin(angle) * r,
                            o.y + math.cos(angle) * r
                        ))
                    elif isinstance(p, FreePointOnLine):
                        loc0 = self.location(p.line.point0)
                        loc1 = self.location(p.line.point1)
                        angle = random.randrange(-99999, 99999, 1) * math.pi / 200000
                        coef = math.tan(angle)
                        add(p, TwoDCoordinates(
                            0.5 * (loc0.x + loc1.x) + coef * (loc0.x - loc1.x),
                            0.5 * (loc0.y + loc1.y) + coef * (loc0.y - loc1.y)
                        ))
                    elif isinstance(p, CirclesIntersection):
                        c0 = self.location(p.circle0.centre)
                        c1 = self.location(p.circle1.centre)
                        r02 = c0.distance2To(self.location(p.circle0.point))
                        r12 = c1.distance2To(self.location(p.circle1.point))
                        # (x - c0.x)^2 + (y - c0.y)^2 == r02
                        # (x - c1.x)^2 + (y - c1.y)^2 == r12
                        # 2x(c1.x - c0.x) + c0.x^2 - c1.x^2 + 2y(c1.y - c0.y) + c0.y^2 - c1.y^2 = r02 - r12
                        if math.fabs(c1.x - c0.x) > 5e-6:
                            # 2x(c1.x - c0.x) = r02 - r12 - c0.x^2 - c0.y^2 + c1.x^2 + c1.y^2 + 2y(c0.y - c1.y)
                            x_coef = 2 * (c1.x - c0.x)
                            y_coef = 2 * (c0.y - c1.y) / x_coef
                            const = (r02 - r12 - c0.x * c0.x - c0.y * c0.y + c1.x * c1.x + c1.y * c1.y) / x_coef
                            # x = const + y_coef * y
                            # (const + y_coef * y - c0.x)^2 + (y - c0.y)^2 == r02
                            # (1 + y_coef^2) * y^2 + 2 (const * y_coef - c0.x * y_coef - c0.y) * y + (const - c0.x)^2 + c0.y^2 - r02
                            a = 1 + y_coef * y_coef
                            b = ((const - c0.x) * y_coef - c0.y)
                            c = (const - c0.x) * (const - c0.x) + c0.y * c0.y - r02
                            # a y^2 + 2b y + c = 0
                            discr = b * b - a * c
                            assert discr >= 0, 'Circles have no intersection points'
                            # y = (-b +- sqrt(discr)) / a
                            #print("%.3f y^2 + %.3f y + %.3f = 0" % (a, 2 * b, c))
                            y_1 = (-b + math.sqrt(discr)) / a
                            y_2 = (-b - math.sqrt(discr)) / a
                            x_1 = const + y_coef * y_1
                            x_2 = const + y_coef * y_2
                        elif math.fabs(c1.y - c0.y) > 5e-6:
                            y_coef = 2 * (c1.y - c0.y)
                            x_coef = 2 * (c0.x - c1.x) / y_coef
                            const = (r02 - r12 - c0.y * c0.y - c0.x * c0.x + c1.y * c1.y + c1.x * c1.x) / y_coef
                            a = 1 + x_coef * x_coef
                            b = ((const - c0.y) * x_coef - c0.x)
                            c = (const - c0.y) * (const - c0.y) + c0.x * c0.x - r02
                            discr = b * b - a * c
                            assert discr >= 0, 'Circles have no intersection points'
                            #print("%.3f x^2 + %.3f x + %.3f = 0" % (a, 2 * b, c))
                            x_1 = -b + math.sqrt(discr) / a
                            x_2 = -b - math.sqrt(discr) / a
                            y_1 = const + x_coef * x_1
                            y_2 = const + x_coef * x_2
                        else:
                            raise PlacementFailedError
                        add(p, [TwoDCoordinates(x_1, y_1), TwoDCoordinates(x_2, y_2)])
                    elif isinstance(p, CentrePoint):
                        coords = [self.location(pt) for pt in p.points]
                        add(p, TwoDCoordinates(
                            sum(c.x for c in coords) / len(coords),
                            sum(c.y for c in coords) / len(coords),
                        ))
                except IncompletePlacementError:
                    pass

    def location(self, point: Point) -> TwoDCoordinates:
        loca = self._coordinates.get(point)
        if loca is None:
            raise IncompletePlacementError
        return loca

    def distance(self, point0, point1):
        if isinstance(point0, str):
            point0 = self.scene.get(point0)
        if isinstance(point1, str):
            point1 = self.scene.get(point1)

        assert isinstance(point0, Point), 'Parameter is not a point'
        assert isinstance(point1, Point), 'Parameter is not a point'

        return self.location(point0).distanceTo(self.location(point1))

    def angle(self, pt0, pt1, pt2, pt3):
        """Angle between vectors (pt0, pt1) and (pt2, pt3)"""
        if isinstance(pt0, str):
            pt0 = self.scene.get(pt0)
        if isinstance(pt1, str):
            pt1 = self.scene.get(pt1)
        if isinstance(pt2, str):
            pt2 = self.scene.get(pt2)
        if isinstance(pt3, str):
            pt3 = self.scene.get(pt3)

        assert isinstance(pt0, Point), 'Parameter is not a pt'
        assert isinstance(pt1, Point), 'Parameter is not a pt'
        assert isinstance(pt2, Point), 'Parameter is not a pt'
        assert isinstance(pt3, Point), 'Parameter is not a pt'

        vec0 = TwoDVector(self.location(pt0), self.location(pt1))
        vec1 = TwoDVector(self.location(pt2), self.location(pt3))
        return vec0.angle(vec1)
