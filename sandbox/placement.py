import numpy as np
from scipy.optimize import minimize

from .core import CoreScene, Constraint

class TwoDCoordinates:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return '(%.5f, %.5f)' % (self.x, self.y)

    def __eq__(self, other):
        return np.fabs(self.x - other.x) < 5e-6 and np.fabs(self.y - other.y) < 5e-6

    def distance_to(self, other):
        return TwoDVector(other, self).length

    def distance2_to(self, other):
        return TwoDVector(other, self).length2

class TwoDVector:
    def __init__(self, start: TwoDCoordinates, end: TwoDCoordinates):
        self.x = end.x - start.x
        self.y = end.y - start.y

    @property
    def length(self):
        return np.hypot(self.x, self.y)

    @property
    def length2(self):
        return self.x ** 2 + self.y ** 2

    def scalar_product(self, other):
        return self.x * other.x + self.y * other.y

    def vector_product(self, other):
        return self.x * other.y - self.y * other.x

    def angle(self, other):
        cos = self.scalar_product(other) / self.length / other.length
        if cos >= 1:
            return 0
        if cos <= -1:
            return np.pi
        return np.arccos(cos) if self.vector_product(other) > 0 else -np.arccos(cos)

class IncompletePlacementError(Exception):
    """Internal error, should never be thrown to public"""

class PlacementFailedError(Exception):
    """Cannot place to meet all the conditions"""

class BasePlacement:
    def length(self, vector):
        start = self.location(vector.start)
        end = self.location(vector.end)
        return np.hypot(end.x - start.x, end.y - start.y)

    def scalar_product(self, vector0, vector1):
        start0 = self.location(vector0.start)
        end0 = self.location(vector0.end)
        start1 = self.location(vector1.start)
        end1 = self.location(vector1.end)
        return (end0.x - start0.x) * (end1.x - start1.x) + (end0.y - start0.y) * (end1.y - start1.y)
        
    def vector_product(self, vector0, vector1):
        start0 = self.location(vector0.start)
        end0 = self.location(vector0.end)
        start1 = self.location(vector1.start)
        end1 = self.location(vector1.end)
        return (end0.x - start0.x) * (end1.y - start1.y) - (end0.y - start0.y) * (end1.x - start1.x)
        
    def vec_angle(self, vector0, vector1):
        cos = self.scalar_product(vector0, vector1) / self.length(vector0) / self.length(vector1)
        if cos >= 1:
            return 0
        if cos <= -1:
            return np.pi
        return np.arccos(cos) if self.vector_product(vector0, vector1) > 0 else -np.arccos(cos)

class Placement(BasePlacement):
    class TempPlacement(BasePlacement):
        def __init__(self, placement, point, coords):
            self._coordinates = dict(placement._coordinates)
            self._coordinates[point] = coords

        def location(self, point: CoreScene.Point) -> TwoDCoordinates:
            loca = self._coordinates.get(point)
            if loca is None:
                raise IncompletePlacementError
            return loca

        def clockwise(self, p0: TwoDCoordinates, p1: TwoDCoordinates, p2: TwoDCoordinates) -> int:
            clo = TwoDVector(p1, p0).vector_product(TwoDVector(p2, p0))
            if clo == 0:
                return 0
            return 1 if clo > 0 else -1

        def validate(self, constraint):
            if constraint.kind == Constraint.Kind.not_equal:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                return np.fabs(pt0.x - pt1.x) >= 5e-6 or np.fabs(pt0.y - pt1.y) >= 5e-6
            if constraint.kind == Constraint.Kind.not_collinear:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                pt2 = self.location(constraint.params[2])
                return self.clockwise(pt0, pt1, pt2) != 0
            if constraint.kind == Constraint.Kind.opposite_side:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                line = constraint.params[2]
                start = self.location(line.point0)
                end = self.location(line.point1)
                clo0 = self.clockwise(start, end, pt0)
                clo1 = self.clockwise(start, end, pt1)
                return clo0 != 0 and clo1 != 0 and clo0 != clo1
            if constraint.kind == Constraint.Kind.same_side:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                line = constraint.params[2]
                start = self.location(line.point0)
                end = self.location(line.point1)
                clo0 = self.clockwise(start, end, pt0)
                clo1 = self.clockwise(start, end, pt1)
                return clo0 != 0 and clo1 != 0 and clo0 == clo1
            if constraint.kind == Constraint.Kind.quadrilateral:
                pt0 = self.location(constraint.params[0])
                pt1 = self.location(constraint.params[1])
                pt2 = self.location(constraint.params[2])
                pt3 = self.location(constraint.params[3])
                clockwise = [self.clockwise(x, y, z) for (x, y, z) in
                             [(pt0, pt1, pt2), (pt1, pt2, pt3), (pt2, pt3, pt0), (pt3, pt0, pt1)]]
                return 0 not in clockwise and sum(clockwise) != 0
            if constraint.kind == Constraint.Kind.convex_polygon:
                points = [self.location(pt) for pt in constraint.params[0]]
                orientation = None
                for index0, pt0 in enumerate(points):
                    for index1, pt1 in enumerate(points[index0 + 1:], start=index0 + 1):
                        for pt2 in points[index1 + 1:]:
                            clockwise = self.clockwise(pt0, pt1, pt2)
                            if clockwise == 0:
                                return False
                            if orientation is None:
                                orientation = clockwise
                            elif orientation != clockwise:
                                return False
                return True
            if constraint.kind == Constraint.Kind.same_direction:
                pt = constraint.params[0]
                vec0 = pt.vector(constraint.params[1])
                vec1 = pt.vector(constraint.params[2])
                return self.scalar_product(vec0, vec1) > 0

            assert False, 'Constraint `%s` not supported in placement' % constraint.kind

    def __init__(self, scene: CoreScene, params=None):
        self.scene = scene
        self._coordinates = {}
        self.params = params if params else {}
        self.__deviation = None
        not_placed = list(scene.points())
        passed_constraints = set()

        def add(p: CoreScene.Point, *coords):
            for candidate in coords:
                temp = Placement.TempPlacement(self, p, candidate)
                for cs in self.scene.validation_constraints:
                    if cs in passed_constraints:
                        continue
                    try:
                        if temp.validate(cs):
                            passed_constraints.add(cs)
                        else:
                            break
                    except IncompletePlacementError:
                        continue
                else:
                    self._coordinates[p] = candidate
                    not_placed.remove(p)
                    return
            raise PlacementFailedError('Cannot meet the constraints')

        while len(not_placed) > 0:
            for p in list(not_placed):
                try:
                    if p.origin == CoreScene.Point.Origin.free:
                        add(p, TwoDCoordinates(
                            np.float128(p.x) if hasattr(p, 'x') else self.__get_coord(p.label + '.x'),
                            np.float128(p.y) if hasattr(p, 'y') else self.__get_coord(p.label + '.y')
                        ))
                    elif p.origin == CoreScene.Point.Origin.circle:
                        o = self.location(p.circle.centre)
                        r = self.radius(p.circle)
                        angle = self.__get_angle(p.label + '.angle')
                        add(p, TwoDCoordinates(
                            o.x + np.sin(angle) * r,
                            o.y + np.cos(angle) * r
                        ))
                    elif p.origin == CoreScene.Point.Origin.line:
                        loc0 = self.location(p.line.point0)
                        loc1 = self.location(p.line.point1)
                        coef = self.__get_coord(p.label + '.coef')
                        add(p, TwoDCoordinates(
                            0.5 * (loc0.x + loc1.x) + coef * (loc0.x - loc1.x),
                            0.5 * (loc0.y + loc1.y) + coef * (loc0.y - loc1.y)
                        ))
                    elif p.origin == CoreScene.Point.Origin.ratio:
                        p0 = self.location(p.point0)
                        p1 = self.location(p.point1)
                        denom = p.coef0 + p.coef1
                        add(p, TwoDCoordinates(
                            (p.coef0 * p0.x + p.coef1 * p1.x) / denom,
                            (p.coef0 * p0.y + p.coef1 * p1.y) / denom
                        ))
                    elif p.origin == CoreScene.Point.Origin.perp:
                        p0 = self.location(p.point)
                        p1 = self.location(p.line.point0)
                        p2 = self.location(p.line.point1)
                        add(p, TwoDCoordinates(
                            p0.x + p1.y - p2.y,
                            p0.y + p2.x - p1.x
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
                        discr = cx0 * cy1 - cx1 * cy0
                        if np.fabs(discr) < 1e-8:
                            raise PlacementFailedError('Lines have no intersection points')
                        s0 = p1.x * p0.y - p1.y * p0.x
                        s1 = p3.x * p2.y - p3.y * p2.x
                        add(p, TwoDCoordinates(
                            (s0 * cy1 - s1 * cy0) / discr,
                            (s1 * cx0 - s0 * cx1) / discr,
                        ))
                    elif p.origin == CoreScene.Point.Origin.circle_x_line:
                        c = self.location(p.circle.centre)
                        r2 = self.radius2(p.circle)
                        p0 = self.location(p.line.point0)
                        p1 = self.location(p.line.point1)
                        # (x - c.x)^2 + (y - c.y)^2 == r2
                        # x = a * p0.x + (1-a) * p1.x
                        # y = a * p0.y + (1-a) * p1.y
                        # (p0.y - p1.y) * x + (p1.x - p0.x) * y = p1.x * p0.y - p1.y * p0.x
                        if np.fabs(p1.x - p0.x) >= 5e-6:
                            # y = ((p0.y - p1.y) * x - (p1.x * p0.y - p1.y * p0.x)) / (p0.x - p1.x)
                            coef_x = (p0.y - p1.y) / (p0.x - p1.x)
                            coef = (p1.x * p0.y - p1.y * p0.x) / (p1.x - p0.x)
                            # y = coef_x * x + coef
                            # (x - c.x)^2 + (coef_x * x + coef - c.y)^2 = r2
                            # (1 + coef_x^2) * x^2 + 2 * (coef_x * (coef - c.y) - c.x) * x + c.x^2 + (coef - c.y)^2 - r2 = 0
                            qa = 1 + coef_x ** 2
                            qb = coef_x * (coef - c.y) - c.x
                            qc = c.x ** 2 + (coef - c.y) ** 2 - r2
                            discr = qb * qb - qa * qc
                            if discr < 0:
                                if discr > -1e-8:
                                    discr = 0
                                else:
                                    raise PlacementFailedError('The line and the circle have no intersection points')
                            # y = (-qb +- sqrt(discr)) / qa
                            sqrt = np.sqrt(discr)
                            x_1 = (-qb + sqrt) / qa
                            x_2 = (-qb - sqrt) / qa
                            y_1 = coef + coef_x * x_1
                            y_2 = coef + coef_x * x_2
                        elif np.fabs(p1.y - p0.y) >= 5e-6:
                            coef_y = (p0.x - p1.x) / (p0.y - p1.y)
                            coef = (p1.y * p0.x - p1.x * p0.y) / (p1.y - p0.y)
                            qa = 1 + coef_y ** 2
                            qb = coef_y * (coef - c.x) - c.y
                            qc = c.y ** 2 + (coef - c.x) ** 2 - r2
                            discr = qb * qb - qa * qc
                            if discr < 0:
                                if discr > -1e-8:
                                    discr = 0
                                else:
                                    raise PlacementFailedError('The line and the circle have no intersection points')
                            sqrt = np.sqrt(discr)
                            y_1 = (-qb + discr) / qa
                            y_2 = (-qb - discr) / qa
                            x_1 = coef + coef_y * y_1
                            x_2 = coef + coef_y * y_2
                        else:
                            raise PlacementFailedError
                        add(p, TwoDCoordinates(x_1, y_1), TwoDCoordinates(x_2, y_2))
                    elif p.origin == CoreScene.Point.Origin.circle_x_circle:
                        c0 = self.location(p.circle0.centre)
                        c1 = self.location(p.circle1.centre)
                        r02 = self.radius2(p.circle0)
                        r12 = self.radius2(p.circle1)
                        # (x - c0.x)^2 + (y - c0.y)^2 == r02
                        # (x - c1.x)^2 + (y - c1.y)^2 == r12
                        # 2x(c1.x - c0.x) + c0.x^2 - c1.x^2 + 2y(c1.y - c0.y) + c0.y^2 - c1.y^2 = r02 - r12
                        if np.fabs(c1.x - c0.x) > 5e-6:
                            # 2x(c1.x - c0.x) = r02 - r12 - c0.x^2 - c0.y^2 + c1.x^2 + c1.y^2 + 2y(c0.y - c1.y)
                            x_coef = 2 * (c1.x - c0.x)
                            y_coef = 2 * (c0.y - c1.y) / x_coef
                            const = (r02 - r12 - c0.x * c0.x - c0.y * c0.y + c1.x * c1.x + c1.y * c1.y) / x_coef
                            # x = const + y_coef * y
                            # (const + y_coef * y - c0.x)^2 + (y - c0.y)^2 == r02
                            # (1 + y_coef^2) * y^2 + 2 (const * y_coef - c0.x * y_coef - c0.y) * y + (const - c0.x)^2 + c0.y^2 - r02
                            a = 1 + y_coef * y_coef
                            b = (const - c0.x) * y_coef - c0.y
                            c = (const - c0.x) ** 2 + c0.y ** 2 - r02
                            # a y^2 + 2b y + c = 0
                            discr = b * b - a * c
                            if discr < 0:
                                if discr > -1e-8:
                                    discr = 0
                                else:
                                    raise PlacementFailedError('The circles have no intersection points')
                            # y = (-b +- sqrt(discr)) / a
                            #print("%.3f y^2 + %.3f y + %.3f = 0" % (a, 2 * b, c))
                            sqrt = np.sqrt(discr)
                            y_1 = (-b + sqrt) / a
                            y_2 = (-b - sqrt) / a
                            x_1 = const + y_coef * y_1
                            x_2 = const + y_coef * y_2
                        elif np.fabs(c1.y - c0.y) > 5e-6:
                            y_coef = 2 * (c1.y - c0.y)
                            x_coef = 2 * (c0.x - c1.x) / y_coef
                            const = (r02 - r12 - c0.y * c0.y - c0.x * c0.x + c1.y * c1.y + c1.x * c1.x) / y_coef
                            a = 1 + x_coef * x_coef
                            b = (const - c0.y) * x_coef - c0.x
                            c = (const - c0.y) ** 2 + c0.x ** 2 - r02
                            discr = b * b - a * c
                            if discr < 0:
                                if discr > -1e-8:
                                    discr = 0
                                else:
                                    raise PlacementFailedError('The circles have no intersection points')
                            #print("%.3f x^2 + %.3f x + %.3f = 0" % (a, 2 * b, c))
                            sqrt = np.sqrt(discr)
                            x_1 = (-b + sqrt) / a
                            x_2 = (-b - sqrt) / a
                            y_1 = const + x_coef * x_1
                            y_2 = const + x_coef * x_2
                        else:
                            raise PlacementFailedError
                        add(p, TwoDCoordinates(x_1, y_1), TwoDCoordinates(x_2, y_2))
                    else:
                        assert False, 'Origin `%s` not supported in placement' % p.origin
                except IncompletePlacementError:
                    pass

    def __get_coord(self, label):
        value = self.params.get(label)
        if value is None:
            value = np.float128(np.tan((np.random.random() - 0.5) * np.pi))
            self.params[label] = value
        return value

    def __get_angle(self, label):
        value = self.params.get(label)
        if value is None:
            value = np.float128(np.random.random() * 2 * np.pi)
            self.params[label] = value
        return value

    def location(self, point) -> TwoDCoordinates:
        if isinstance(point, str):
            point = self.scene.get(point)
        assert isinstance(point, CoreScene.Point), 'Parameter is not a point'

        loca = self._coordinates.get(point)
        if loca is None:
            raise IncompletePlacementError
        return loca

    def radius(self, circle):
        if isinstance(circle, str):
            circle = self.scene.get(circle)
        return self.length(circle.radius_start.vector(circle.radius_end))

    def radius2(self, circle):
        if isinstance(circle, str):
            circle = self.scene.get(circle)
        return self.location(circle.radius_start).distance2_to(self.location(circle.radius_end))

    def distance(self, point0, point1):
        if isinstance(point0, str):
            point0 = self.scene.get(point0)
        if isinstance(point1, str):
            point1 = self.scene.get(point1)

        assert isinstance(point0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(point1, CoreScene.Point), 'Parameter is not a point'

        return self.length(point0.vector(point1))

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

        assert isinstance(pt0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt1, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt2, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt3, CoreScene.Point), 'Parameter is not a point'

        return self.vec_angle(pt0.vector(pt1), pt2.vector(pt3))

    def dump(self):
        if self.params:
            print('Parameters:')
            print('\n'.join([('\t%s => %.5f' % (label, self.params[label])) for label in self.params]))
            print('')
        print('Coordinates:')
        print('\n'.join([('\t%s => %s' % (pt.label, self.location(pt))) for pt in self.scene.points()]))
        print('\nDeviation: %.15f' % self.deviation())

    def deviation(self):
        if self.__deviation:
            return self.__deviation

        has_distance_constraint = False
        dist_square = 0.0
        numb_square = 0.0
        for cnstr in self.scene.adjustment_constraints:
            if hasattr(cnstr, 'guaranteed') and cnstr.guaranteed:
                continue

            if cnstr.kind == Constraint.Kind.distance:
                has_distance_constraint = True
                pt0 = cnstr.params[0]
                pt1 = cnstr.params[1]
                dist_square += (self.length(pt0.vector(pt1)) - np.float128(cnstr.params[2])) ** 2
            elif cnstr.kind == Constraint.Kind.distances_ratio:
                pt0 = cnstr.params[0]
                pt1 = cnstr.params[1]
                pt2 = cnstr.params[2]
                pt3 = cnstr.params[3]
                coef0 = np.float128(cnstr.params[4])
                coef1 = np.float128(cnstr.params[5])
                numb_square += (self.length(pt0.vector(pt1)) / self.length(pt2.vector(pt3)) - coef1 / coef0) ** 2
            elif cnstr.kind == Constraint.Kind.collinear:
                pt = cnstr.params[0]
                vec0 = pt.vector(cnstr.params[1])
                vec1 = pt.vector(cnstr.params[2])
                numb_square += (self.vector_product(vec0, vec1) / self.length(vec0) / self.length(vec1)) ** 2
            elif cnstr.kind == Constraint.Kind.perpendicular:
                pt0 = self.location(cnstr.params[0].point0)
                pt1 = self.location(cnstr.params[0].point1)
                pt2 = self.location(cnstr.params[1].point0)
                pt3 = self.location(cnstr.params[1].point1)
                vec0 = TwoDVector(pt0, pt1)
                vec1 = TwoDVector(pt2, pt3)
                numb_square += vec0.scalar_product(vec1) ** 2 / vec0.length2 / vec1.length2
            elif cnstr.kind == Constraint.Kind.angles_ratio:
                vec0 = cnstr.params[0].vector(cnstr.params[1])
                vec1 = cnstr.params[2].vector(cnstr.params[3])
                vec2 = cnstr.params[4].vector(cnstr.params[5])
                vec3 = cnstr.params[6].vector(cnstr.params[7])
                ratio = cnstr.params[8]
                numb_square += (self.vec_angle(vec0, vec1) - self.vec_angle(vec2, vec3) * ratio) ** 2
            else:
                assert False, 'Constraint `%s` not supported in adjustment' % cnstr.kind

        if not has_distance_constraint:
            self.__deviation = numb_square
        else:
            self.__deviation = dist_square
            if numb_square > 0:
                average2 = 0.0
                points = [self.location(pt) for pt in self.scene.points(skip_auxiliary=True)]
                for index, pt0 in enumerate(points):
                    for pt1 in points[index + 1:]:
                        average2 += pt0.distance2_to(pt1)
                average2 /= len(points) * (len(points) - 1) / 2
                self.__deviation += numb_square * average2

        return self.__deviation

def iterative_placement(scene, max_attempts=10000, max_iterations=400, print_progress=False):
    for attempt in range(0, max_attempts):
        try:
            placement = Placement(scene)
            if placement.deviation() < 1e-14:
                return placement
            keys = list(placement.params.keys())
            def placement_for_data(data):
                return Placement(scene, dict(zip(keys, data)))

            def numpy_fun(data):
                return placement_for_data(data).deviation()

            data = np.array([placement.params[k] for k in keys])
            res = minimize(numpy_fun, data, method='BFGS', options={'gtol': 1e-7, 'maxiter': max_iterations, 'disp': print_progress})
            pl = placement_for_data(res.x)
            if pl.deviation() < 1e-14:
                return pl
        except PlacementFailedError as e:
            if print_progress:
                print('Attempt %d failed: %s\r' % (attempt, e))
    return None
