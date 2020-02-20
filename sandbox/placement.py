from functools import reduce
import mpmath
from mpmath import mpf
from typing import Set

from .core import CoreScene, Constraint

class TwoDCoordinates:
    def __init__(self, x: mpf, y: mpf):
        self.x = x
        self.y = y

    def __str__(self):
        return '(%.5f, %.5f)' % (self.x, self.y)

    def __eq__(self, other):
        return mpmath.fabs(self.x - other.x) < 5e-6 and mpmath.fabs(self.y - other.y) < 5e-6

    def distanceTo(self, other) -> mpf:
        return TwoDVector(other, self).length

    def distance2To(self, other) -> mpf:
        return TwoDVector(other, self).length2

class TwoDVector:
    def __init__(self, start: TwoDCoordinates, end: TwoDCoordinates):
        self.x = end.x - start.x
        self.y = end.y - start.y

    @property
    def length(self) -> mpf:
        return mpmath.hypot(self.x, self.y)

    @property
    def length2(self) -> mpf:
        return self.x ** 2 + self.y ** 2

    def scalar_product(self, other) -> mpf:
        return self.x * other.x + self.y * other.y

    def vector_product(self, other) -> mpf:
        return self.x * other.y - self.y * other.x

    def angle(self, other) -> mpf:
        cos = self.scalar_product(other) / self.length / other.length
        if cos >= 1:
            return 0
        elif cos <= -1:
            return mpmath.pi
        else:
            return mpmath.acos(cos) if self.vector_product(other) > 0 else -mpmath.acos(cos)

class IncompletePlacementError(Exception):
    """Internal error, should never be thrown to public"""

class PlacementFailedError(Exception):
    """Cannot place to meet all the conditions"""

class Placement:
    class Parameters:
        def __init__(self, params = None):
            self.coords = dict(params.coords) if params else {}
            self.angles = dict(params.angles) if params else {}

        def get_coord(self, label):
            value = self.coords.get(label)
            if value is None:
                value = mpmath.tan(mpmath.rand() * mpmath.pi - mpmath.pi / 2)
                self.coords[label] = value
            return value

        def get_angle(self, label):
            value = self.angles.get(label)
            if value is None:
                value = mpmath.rand() * 2 * mpmath.pi
                self.angles[label] = value
            return value

    class TempPlacement:
        def __init__(self, placement, point, coords):
            self._coordinates = dict(placement._coordinates)
            self._coordinates[point] = coords

        def location(self, point: CoreScene.Point) -> TwoDCoordinates:
            loca = self._coordinates.get(point)
            if loca is None:
                raise IncompletePlacementError
            return loca

        def validate(self, constraint):
            if constraint.kind == Constraint.Kind.not_equal:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                return mpmath.fabs(pt0.x - pt1.x) >= 5e-6 or mpmath.fabs(pt0.y - pt1.y) >= 5e-6
            elif constraint.kind == Constraint.Kind.opposite_side:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                line = constraint.params[2]
                start = self.location(line.point0)
                end = self.location(line.point1)

                def clockwise(p0: TwoDCoordinates, p1: TwoDCoordinates, p2: TwoDCoordinates) -> bool:
                    return TwoDVector(p1, p0).vector_product(TwoDVector(p2, p0)) < 0

                return clockwise(start, end, pt0) != clockwise(start, end, pt1)
            else:
                raise PlacementFailedError('Constraint `%s` not supported in placement' % constraint.kind)

    def __init__(self, scene: CoreScene, params = None):
        self.scene = scene
        self._coordinates = {}
        self.params = params if params else Placement.Parameters()
        not_placed: Set[CoreScene.Point] = set(scene.points())

        def add(p: CoreScene.Point, *coords):
            for candidate in coords:
                temp = Placement.TempPlacement(self, p, candidate)
                if all(temp.validate(cs) for cs in p.constraints):
                    self._coordinates[p] = candidate
                    not_placed.remove(p)
                    return
            raise PlacementFailedError('Cannot meet the constraints')

        while len(not_placed) > 0:
            for p in list(not_placed):
                try:
                    if p.origin == CoreScene.Point.Origin.free:
                        add(p, TwoDCoordinates(
                            p.x if hasattr(p, 'x') else self.params.get_coord(p.label + '.x'),
                            p.y if hasattr(p, 'y') else self.params.get_coord(p.label + '.y')
                        ))
                    elif p.origin == CoreScene.Point.Origin.circle:
                        o = self.location(p.circle.centre)
                        r = self.location(p.circle.radius_start).distanceTo(self.location(p.circle.radius_end))
                        angle = self.params.get_angle(p.label + '.angle')
                        add(p, TwoDCoordinates(
                            o.x + mpmath.sin(angle) * r,
                            o.y + mpmath.cos(angle) * r
                        ))
                    elif p.origin == CoreScene.Point.Origin.line:
                        loc0 = self.location(p.line.point0)
                        loc1 = self.location(p.line.point1)
                        coef = self.params.get_coord(p.label + '.coef')
                        add(p, TwoDCoordinates(
                            0.5 * (loc0.x + loc1.x) + coef * (loc0.x - loc1.x),
                            0.5 * (loc0.y + loc1.y) + coef * (loc0.y - loc1.y)
                        ))
                    elif p.origin == CoreScene.Point.Origin.ratio:
                        p0 = self.location(p.point0)
                        p1 = self.location(p.point1)
                        add(p, TwoDCoordinates(
                            (p.coef0 * p0.x + p.coef1 * p1.x) / (p.coef0 + p.coef1),
                            (p.coef0 * p0.y + p.coef1 * p1.y) / (p.coef0 + p.coef1)
                        ))
                    elif p.origin == CoreScene.Point.Origin.line_x_line:
                        p0 = self.location(p.line0.point0)
                        p1 = self.location(p.line0.point1)
                        p2 = self.location(p.line1.point0)
                        p3 = self.location(p.line1.point1)
                        # x = a * p0.x + (1-a) * p1.x
                        # y = a * p0.y + (1-a) * p1.y
                        # x = b * p2.x + (1-b) * p3.x
                        # y = b * p2.y + (1-b) * p3.y

                        # x = p1.x + a * (p0.x - p1.x) | *(p0.y - p1.y)
                        # y = p1.y + a * (p0.y - p1.y) | *(p0.x - p1.x)
                        # (p0.y - p1.y) * x + (p1.x - p0.x) * y = p1.x * p0.y - p1.y * p0.x
                        # (p2.y - p3.y) * x + (p3.x - p2.x) * y = p3.x * p2.y - p3.y * p2.x
                        cx0 = p0.y - p1.y
                        cy0 = p1.x - p0.x
                        cx1 = p2.y - p3.y
                        cy1 = p3.x - p2.x
                        s0 = p1.x * p0.y - p1.y * p0.x
                        s1 = p3.x * p2.y - p3.y * p2.x
                        discr = cx0 * cy1 - cx1 * cy0
                        if mpmath.fabs(discr) < 1e-8:
                            raise PlacementFailedError('Lines have no intersection points')
                        add(p, TwoDCoordinates(
                            (s0 * cy1 - s1 * cy0) / discr,
                            (s1 * cx0 - s0 * cx1) / discr,
                        ))
                    elif p.origin == CoreScene.Point.Origin.circle_x_line:
                        c = self.location(p.circle.centre)
                        r2 = self.location(p.circle.radius_start).distance2To(self.location(p.circle.radius_end))
                        p0 = self.location(p.line.point0)
                        p1 = self.location(p.line.point1)
                        # (x - c.x)^2 + (y - c.y)^2 == r2
                        # x = a * p0.x + (1-a) * p1.x
                        # y = a * p0.y + (1-a) * p1.y
                        # (p0.y - p1.y) * x + (p1.x - p0.x) * y = p1.x * p0.y - p1.y * p0.x
                        if mpmath.fabs(p1.x - p0.x) >= 5e-6:
                            # y = ((p0.y - p1.y) * x - (p1.x * p0.y - p1.y * p0.x)) / (p0.x - p1.x)
                            coef_x = (p0.y - p1.y) / (p0.x - p1.x)
                            coef = (p1.x * p0.y - p1.y * p0.x) / (p1.x - p0.x)
                            # y = coef_x * x + coef
                            # (x - c.x)^2 + (coef_x * x + coef - c.y)^2 = r2
                            # (1 + coef_x^2) * x^2 + 2 * (coef_x * (coef - c.y) - c.x) * x + c.x^2 + (coef - c.y)^2 - r2 = 0
                            qa = 1 + coef_x * coef_x
                            qb = coef_x * (coef - c.y) - c.x
                            qc = c.x ** 2 + (coef - c.y) ** 2 - r2
                            discr = qb * qb - qa * qc
                            if discr < 0:
                                raise PlacementFailedError('The line and the circle have no intersection points')
                            # y = (-qb +- sqrt(discr)) / qa
                            x_1 = (-qb + mpmath.sqrt(discr)) / qa
                            x_2 = (-qb - mpmath.sqrt(discr)) / qa
                            y_1 = coef + coef_x * x_1
                            y_2 = coef + coef_x * x_2
                        elif mpmath.fabs(p1.y - p0.y) >= 5e-6:
                            coef_y = (p0.x - p1.x) / (p0.y - p1.y)
                            coef = (p1.y * p0.x - p1.x * p0.y) / (p1.y - p0.y)
                            qa = 1 + coef_y * coef_y
                            qb = coef_y * (coef - c.x) - c.y
                            qc = c.y * c.y + (coef - c.x) * (coef - c.x) - r2
                            discr = qb * qb - qa * qc
                            if discr < 0:
                                raise PlacementFailedError('The line and the circle have no intersection points')
                            y_1 = (-qb + mpmath.sqrt(discr)) / qa
                            y_2 = (-qb - mpmath.sqrt(discr)) / qa
                            x_1 = coef + coef_y * y_1
                            x_2 = coef + coef_y * y_2
                        else:
                            raise PlacementFailedError
                        add(p, TwoDCoordinates(x_1, y_1), TwoDCoordinates(x_2, y_2))
                    elif p.origin == CoreScene.Point.Origin.circle_x_circle:
                        c0 = self.location(p.circle0.centre)
                        c1 = self.location(p.circle1.centre)
                        r02 = self.location(p.circle0.radius_start).distance2To(self.location(p.circle0.radius_end))
                        r12 = self.location(p.circle1.radius_start).distance2To(self.location(p.circle1.radius_end))
                        # (x - c0.x)^2 + (y - c0.y)^2 == r02
                        # (x - c1.x)^2 + (y - c1.y)^2 == r12
                        # 2x(c1.x - c0.x) + c0.x^2 - c1.x^2 + 2y(c1.y - c0.y) + c0.y^2 - c1.y^2 = r02 - r12
                        if mpmath.fabs(c1.x - c0.x) > 5e-6:
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
                            if discr < 0:
                                raise PlacementFailedError('The circles have no intersection points')
                            # y = (-b +- sqrt(discr)) / a
                            #print("%.3f y^2 + %.3f y + %.3f = 0" % (a, 2 * b, c))
                            y_1 = (-b + mpmath.sqrt(discr)) / a
                            y_2 = (-b - mpmath.sqrt(discr)) / a
                            x_1 = const + y_coef * y_1
                            x_2 = const + y_coef * y_2
                        elif mpmath.fabs(c1.y - c0.y) > 5e-6:
                            y_coef = 2 * (c1.y - c0.y)
                            x_coef = 2 * (c0.x - c1.x) / y_coef
                            const = (r02 - r12 - c0.y * c0.y - c0.x * c0.x + c1.y * c1.y + c1.x * c1.x) / y_coef
                            a = 1 + x_coef * x_coef
                            b = ((const - c0.y) * x_coef - c0.x)
                            c = (const - c0.y) * (const - c0.y) + c0.x * c0.x - r02
                            discr = b * b - a * c
                            if discr < 0:
                                raise PlacementFailedError('The circles have no intersection points')
                            #print("%.3f x^2 + %.3f x + %.3f = 0" % (a, 2 * b, c))
                            x_1 = -b + mpmath.sqrt(discr) / a
                            x_2 = -b - mpmath.sqrt(discr) / a
                            y_1 = const + x_coef * x_1
                            y_2 = const + x_coef * x_2
                        else:
                            raise PlacementFailedError
                        add(p, TwoDCoordinates(x_1, y_1), TwoDCoordinates(x_2, y_2))
                    else:
                        raise PlacementFailedError('Origin `%s` not supported in placement' % p.origin)
                except IncompletePlacementError:
                    pass

    def location(self, point: CoreScene.Point) -> TwoDCoordinates:
        loca = self._coordinates.get(point)
        if loca is None:
            raise IncompletePlacementError
        return loca

    def distance(self, point0, point1):
        if isinstance(point0, str):
            point0 = self.scene.get(point0)
        if isinstance(point1, str):
            point1 = self.scene.get(point1)

        assert isinstance(point0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(point1, CoreScene.Point), 'Parameter is not a point'

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

        assert isinstance(pt0, CoreScene.Point), 'Parameter is not a pt'
        assert isinstance(pt1, CoreScene.Point), 'Parameter is not a pt'
        assert isinstance(pt2, CoreScene.Point), 'Parameter is not a pt'
        assert isinstance(pt3, CoreScene.Point), 'Parameter is not a pt'

        vec0 = TwoDVector(self.location(pt0), self.location(pt1))
        vec1 = TwoDVector(self.location(pt2), self.location(pt3))
        return vec0.angle(vec1)

    def dump(self):
        print('Parameters:')
        if self.params.coords:
            print('\n'.join([('%s => %.5f' % (label, self.params.coords[label])) for label in self.params.coords]))
        if self.params.angles:
            print('\n'.join([('%s => %.5f' % (label, self.params.angles[label])) for label in self.params.angles]))
        print('\nCoordinates:')
        print('\n'.join([('%s => %s' % (pt.label, self.location(pt))) for pt in self.scene.points()]))
        print('\nDeviation: %.5f' % self.deviation())

    def deviation(self):
        square = 0.0
        for cnstr in self.scene.constraints:
            if cnstr.kind == Constraint.Kind.distance:
                pt0 = self.location(cnstr.params[0])
                pt1 = self.location(cnstr.params[1])
                square += (pt0.distanceTo(pt1) - cnstr.params[2]) ** 2
            else:
                raise PlacementFailedError('Constraint `%s` not supported in adjustment' % cnstr.kind)
        return mpmath.sqrt(square)

    def iterate(self):
        keys = list(self.params.coords.keys()) + list(self.params.angles.keys())

        gradient = []
        for index in range(0, len(self.params.coords)):
            key = keys[index]
            params = Placement.Parameters(self.params)
            params.coords[key] = self.params.coords[key] + mpf(1e-10)
            test = Placement(self.scene, params)
            gradient.append(test.deviation() - self.deviation())
        for index in range(len(self.params.coords), len(keys)):
            key = keys[index]
            params = Placement.Parameters(self.params)
            params.angles[key] = self.params.angles[key] + mpf(1e-10)
            test = Placement(self.scene, params)
            gradient.append(test.deviation() - self.deviation())
        #length = mpmath.sqrt(mpmath.nsum((lambda x: x ** 2), *gradient))
        length = mpmath.sqrt(reduce((lambda s, x : s + x ** 2), gradient, 0))
        if length > 0:
            gradient = [d * mpf('1.e-10') / length for d in gradient]

        deg = 0
        previous = self
        while True:
            coef = 2 ** deg
            params = Placement.Parameters(self.params)
            for index in range(0, len(self.params.coords)):
                key = keys[index]
                params.coords[key] = self.params.coords[key] - gradient[index] * coef
            for index in range(len(self.params.coords), len(keys)):
                key = keys[index]
                params.angles[key] = self.params.angles[key] - gradient[index] * coef
            test = Placement(self.scene, params)
            if test.deviation() > previous.deviation():
                return previous
            previous = test
            deg += 1
