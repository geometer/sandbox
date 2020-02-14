import math
import random
from typing import Dict, List, Set

from .objects import Object, Scene
from .objects import Point, FreePoint, PointOnLine, CentrePoint, CirclesIntersection
from .objects import Line, Circle

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

    def scalarProduct(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def vectorProduct(self, other) -> float:
        return self.x * other.y - self.y * other.x

    def angle(self, other) -> float:
        cos = self.scalarProduct(other) / self.length / other.length
        if cos >= 1:
            return 0
        elif cos <= -1:
            return math.pi / 2 if self.vectorProduct(other) > 0 else -math.pi / 2
        else:
            return math.acos(cos) if self.vectorProduct(other) > 0 else -math.acos(cos)

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

        def add_list(p: Point, coords: List[TwoDCoordinates]):
            for candidate in coords:
                temp = Placement.TempPlacement(self, p, candidate)
                if all(cs.validate(temp) for cs in p.constraints):
                    self._coordinates[p] = candidate
                    not_placed.remove(p)
                    return
            raise PlacementFailedError

        def add(p: Point, coord: TwoDCoordinates):
            add_list(p, [coord])

        while len(not_placed) > 0:
            for p in list(not_placed):
                try:
                    if isinstance(p, FreePoint):
                        add(p, TwoDCoordinates(
                            p.x if hasattr(p, 'x') else random.randrange(0, 100000, 1) / 1000.0,
                            p.y if hasattr(p, 'y') else random.randrange(0, 100000, 1) / 1000.0
                        ))
                    elif isinstance(p, PointOnLine):
                        c0 = self.location(p.point0)
                        c1 = self.location(p.point1)
                        add(p, TwoDCoordinates(
                            c0.x * p.ratio + c1.x * (1 - p.ratio),
                            c0.y * p.ratio + c1.y * (1 - p.ratio)
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
                            y1 = (-b + math.sqrt(discr)) / a
                            y2 = (-b - math.sqrt(discr)) / a
                            x1 = const + y_coef * y1
                            x2 = const + y_coef * y2
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
                            x1 = -b + math.sqrt(discr) / a
                            x2 = -b - math.sqrt(discr) / a
                            y1 = const + x_coef * x1
                            y2 = const + x_coef * x2
                        else:
                            raise PlacementFailedError
                        #print('(%.3f, %.3f), (%.3f, %.3f)' % (y1, x1, y2, x2))
                        add_list(p, [TwoDCoordinates(x1, y1), TwoDCoordinates(x2, y2)])
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

        v0 = TwoDVector(self.location(pt0), self.location(pt1))
        v1 = TwoDVector(self.location(pt2), self.location(pt3))
        return v0.angle(v1)
