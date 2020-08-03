from enum import Enum, auto
import itertools

import numpy as np
import sympy as sp

from .figure import Figure, Circle
from .scene import Scene
from .util import Comment, divide, normalize_number, keys_for_triangle

class Property:
    def __init__(self, property_key, point_set):
        self.property_key = property_key
        self.point_set = point_set
        self.__hash = None
        self.__reason = None
        self.__alternate_reasons = []
        self.bases = []

    def __acceptable_reason(self, value):
        while True:
            lesser = value.all_premises.get(self)
            if lesser:
                value = lesser.reason
            else:
                return value

    def add_base(self, base):
        if base not in self.bases:
            self.bases.append(base)

    @property
    def reason(self):
        return self.__reason

    @property
    def proper_reasons(self):
        return [self.__reason] + self.__alternate_reasons

    @property
    def alternate_reasons(self):
        if self.bases:
            alt = set(self.__alternate_reasons)
            for base in self.bases:
                alt.add(base.reason)
                alt.update(set(base.alternate_reasons))
            return list(alt)
        return self.__alternate_reasons

    @reason.setter
    def reason(self, value):
        self.__set_reason(self.__acceptable_reason(value))

    def __set_reason(self, value):
        if self.__reason == value:
            return

        if self.__reason:
            self.__alternate_reasons.append(self.__reason)

        if value in self.__alternate_reasons:
            self.__alternate_reasons.remove(value)
        self.__reason = value

    def merge(self, other_prop):
        assert self == other_prop, '`%s` != `%s`' % (self, other_prop)
        self.add_reason(other_prop.reason)
        for reason in other_prop.__alternate_reasons:
            self.add_reason(reason)
        if other_prop.bases:
            for base in other_prop.bases:
                self.add_base(base)

    def optimize(self):
        candidate = None
        cost = self.reason.cost
        for reason in self.alternate_reasons:
            reason.reset_premises()
            if reason.cost < cost:
                cost = reason.cost
                candidate = reason
        if candidate:
            self.__set_reason(candidate)
            return True
        return False

    def add_reason(self, reason, optimize=True):
        reason = self.__acceptable_reason(reason)
        if self.__reason is None:
            self.__set_reason(reason)
        elif reason == self.__reason:
            return
        elif optimize and reason.cost < self.__reason.cost:
            self.__set_reason(reason)
        elif reason not in self.alternate_reasons:
            self.__alternate_reasons.append(reason)

    @property
    def priority(self):
        if self.reason.rule:
            return self.__priority__ * self.reason.rule.priority()
        else:
            return self.__priority__ * 2

    @property
    def __priority__(self):
        return 3

    def keys(self):
        return []

    def stringify(self, printer):
        return self.description.stringify(printer)

    def compare_values(self, other):
        return True

    def __str__(self):
        return str(self.description)

    def __eq__(self, other):
        return type(self) == type(other) and self.property_key == other.property_key

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(type(self)) + hash(self.property_key)
        return self.__hash

class PointAndCircleProperty(Property):
    """
    Point location relative to circle
    """
    class Kind(Enum):
        inside  = auto()
        on      = auto()
        outside = auto()

        def __str__(self):
            return self.name

    @staticmethod
    def unique_key(point, cpoints_set):
        return (point, cpoints_set)

    def __init__(self, point, cpoint0, cpoint1, cpoint2, location):
        self.point = point
        self.circle_key = frozenset((cpoint0, cpoint1, cpoint2))
        self.location = location
        super().__init__(PointAndCircleProperty.unique_key(self.point, self.circle_key), {point, cpoint0, cpoint1, cpoint2})

    def keys(self):
        return self.property_key

    @property
    def description(self):
        if self.location == PointAndCircleProperty.Kind.inside:
            pattern ='$%{point:pt}$ lies inside $%{circle:circ}$'
        elif self.location == PointAndCircleProperty.Kind.outside:
            pattern ='$%{point:pt}$ lies outside of $%{circle:circ}$'
        elif self.location == PointAndCircleProperty.Kind.on:
            pattern ='$%{point:pt}$ lies on $%{circle:circ}$'
        return Comment(pattern, {'pt': self.point, 'circ': Circle(*self.circle_key)})

    def compare_values(self, other):
        return self.location == other.location

class CircleCoincidenceProperty(Property):
    """
    Two circles (defined by triples of points) are [not] coincident
    """
    def __init__(self, triple0, triple1, coincident):
        self.circle_keys = (frozenset(triple0), frozenset(triple1))
        super().__init__(frozenset(self.circle_keys), {*triple0, *triple1})
        self.coincident = coincident

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        if self.coincident:
            pattern = '$%{circle:c0}$ coincides with $%{circle:c1}$'
        else:
            pattern = '$%{circle:c0}$ and $%{circle:c1}$ differ'
        return Comment(
            pattern, {'c0': Circle(*self.circle_keys[0]), 'c1': Circle(*self.circle_keys[1])}
        )

    def compare_values(self, other):
        return self.coincident == other.coincident

class ConcyclicPointsProperty(Property):
    """
    Concyclic points
    """
    def __init__(self, *points):
        assert len(points) >= 4
        self.points = points
        super().__init__(frozenset(self.points), set(points))

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        patterns = ['$%{point:' + str(i) + '}$' for i in range(0, len(self.points))]
        return Comment(
            'Points ' + ', '.join(patterns[:-1]) + ', and ' + patterns[-1] + ' are concyclic',
            dict((str(index), pt) for index, pt in enumerate(self.points))
        )

class PointOnLineProperty(Property):
    """
    A point lies [not] on a line
    """
    def __init__(self, point, segment, on_line):
        super().__init__((point, segment), {point, *segment.points})
        self.point = point
        self.segment = segment
        self.on_line = on_line

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        if self.on_line:
            pattern = '$%{point:point}$ lies on line $%{line:line}$'
        else:
            pattern = '$%{point:point}$ does not lie on line $%{line:line}$'
        return Comment(pattern, {'point': self.point, 'line': self.segment})

    def compare_values(self, other):
        return self.on_line == other.on_line

class LinesCoincidenceProperty(Property):
    """
    Two lines (defined by segments) are [not] coincident
    """
    def __init__(self, segment0, segment1, coincident):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments), {*segment0.points, *segment1.points})
        self.coincident = coincident

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        if self.coincident:
            pattern = '$%{line:line0}$ is the same line as $%{line:line1}$'
        else:
            pattern = '$%{line:line0}$ and $%{line:line1}$ are different lines'
        return Comment(pattern, {'line0': self.segments[0], 'line1': self.segments[1]})

    def compare_values(self, other):
        return self.coincident == other.coincident

class PointsCollinearityProperty(Property):
    """
    [Not] collinear points
    """
    def __init__(self, point0, point1, point2, collinear):
        self.points = (point0, point1, point2)
        super().__init__(frozenset(self.points), {point0, point1, point2})
        self.collinear = collinear

    @property
    def __priority__(self):
        return 1

    def keys(self, lengths=None):
        return keys_for_triangle(Scene.Triangle(*self.points), lengths)

    @property
    def description(self):
        if self.collinear:
            pattern = 'Points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are collinear'
        else:
            pattern = 'Points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are not collinear'
        return Comment(pattern, {'pt0': self.points[0], 'pt1': self.points[1], 'pt2': self.points[2]})

    def compare_values(self, other):
        return self.collinear == other.collinear

class MultiPointsCollinearityProperty(Property):
    """
    Collinear points
    """
    def __init__(self, *points):
        self.points = tuple(points)
        super().__init__(frozenset(points), set(points))

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        patterns = ['$%{point:' + str(i) + '}$' for i in range(0, len(self.points))]
        return Comment(
            'Points ' + ', '.join(patterns[:-1]) + ', and ' + patterns[-1] + ' are collinear',
            dict((str(index), pt) for index, pt in enumerate(self.points))
        )

class ParallelVectorsProperty(Property):
    """
    Two vectors are parallel (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vectors = (vector0, vector1)
        super().__init__(frozenset(self.vectors), {*vector0.points, *vector1.points})

    def keys(self):
        return [self.vectors[0].as_segment, self.vectors[1].as_segment]

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return Comment(
            '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
            {'vec0': self.vectors[0], 'vec1': self.vectors[1]}
        )

class ParallelSegmentsProperty(Property):
    """
    Two segments are parallel (or at least one of them has zero length)
    """
    def __init__(self, segment0, segment1):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments), {*segment0.points, *segment1.points})

    def keys(self):
        return self.segments

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return Comment(
            '$%{segment:seg0} \\,\\|\\, %{segment:seg1}$',
            {'seg0': self.segments[0], 'seg1': self.segments[1]}
        )

class PerpendicularSegmentsProperty(Property):
    """
    Two segments are perpendicular (or at least one of them has zero length)
    """
    def __init__(self, segment0, segment1):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments), {*segment0.points, *segment1.points})

    def keys(self):
        return self.segments

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return Comment(
            '$%{segment:seg0} \\perp %{segment:seg1}$',
            {'seg0': self.segments[0], 'seg1': self.segments[1]}
        )

    def verify(self, placement):
        vec0 = self.segments[0].points[0].vector(self.segments[0].points[1])
        vec1 = self.segments[1].points[0].vector(self.segments[1].points[1])
        return np.fabs(placement.scalar_product(vec0, vec1)) < 1e-8

class PointsCoincidenceProperty(Property):
    """
    [Not] coincident points
    """
    def __init__(self, point0, point1, coincident):
        assert isinstance(point0, Scene.Point)
        assert isinstance(point1, Scene.Point)
        assert point0 != point1
        self.points = [point0, point1]
        super().__init__(frozenset(self.points), {point0, point1})
        self.coincident = coincident

    @property
    def __priority__(self):
        return 3 if self.coincident else 1

    def keys(self):
        return [self.points[0].segment(self.points[1]), *self.points]

    @property
    def description(self):
        if self.coincident:
            pattern = 'Points $%{point:pt0}$ and $%{point:pt1}$ are coincident'
        else:
            pattern = 'Points $%{point:pt0}$ and $%{point:pt1}$ are not coincident'
        return Comment(pattern, {'pt0': self.points[0], 'pt1': self.points[1]})

    def compare_values(self, other):
        return self.coincident == other.coincident

class SameOrOppositeSideProperty(Property):
    """
    Two points on opposite/same sides of a line
    """
    @staticmethod
    def unique_key(segment, point0, point1):
        return frozenset([segment, point0, point1])

    def __init__(self, segment, point0, point1, same):
        self.segment = segment
        self.points = (point0, point1)
        self.same = same
        super().__init__(SameOrOppositeSideProperty.unique_key(segment, point0, point1), {point0, point1, *segment.points})

    @property
    def __priority__(self):
        return 1

    def keys(self):
        return [self.segment]

    @property
    def description(self):
        if self.same:
            pattern = '$%{point:pt0}$, $%{point:pt1}$ located on the same side of line $%{line:line}$'
        else:
            pattern = '$%{point:pt0}$, $%{point:pt1}$ located on opposite sides of line $%{line:line}$'
        return Comment(pattern, {'pt0': self.points[0], 'pt1': self.points[1], 'line': self.segment})

    def compare_values(self, other):
        return self.same == other.same

class PointInsideAngleProperty(Property):
    """
    Point lies inside an angle
    """
    @staticmethod
    def unique_key(point, angle):
        return (point, angle)

    def __init__(self, point, angle):
        self.point = point
        self.angle = angle
        super().__init__(PointInsideAngleProperty.unique_key(point, angle), {point, *angle.point_set})

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return Comment('$%{point:pt}$ lies inside $%{angle:angle}$', {'pt': self.point, 'angle': self.angle})

    def keys(self):
        return [self.point, self.angle]

class PointInsideTriangleProperty(Property):
    """
    Point lies inside a triangle
    """
    def __init__(self, point, triangle):
        self.point = point
        self.triangle = triangle
        super().__init__((point, triangle.symmetric_key), {point, *triangle.points})

    @property
    def __priority__(self):
        return 2

    @property
    def description(self):
        return Comment('$%{point:pt}$ lies inside $%{triangle:triangle}$', {'pt': self.point, 'triangle': self.triangle})

class PointInsideSquareProperty(Property):
    """
    Point lies inside a square
    """
    def __init__(self, point, square):
        self.point = point
        self.square = square
        super().__init__((point, frozenset(square.points)), {point, *square.points})

    @property
    def __priority__(self):
        return 2

    @property
    def description(self):
        return Comment('$%{point:pt}$ lies inside square $%{polygon:square}$', {'pt': self.point, 'square': self.square})

class EquilateralTriangleProperty(Property):
    """
    Equilateral triangle
    """
    def __init__(self, points):
        self.triangle = points if isinstance(points, Scene.Triangle) else Scene.Triangle(*points)
        super().__init__(self.triangle.symmetric_key, {*self.triangle.points})

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def __priority__(self):
        return 4.5

    @property
    def description(self):
        return Comment('$%{triangle:triangle}$ is equilateral', {'triangle': self.triangle})

class QuadrilateralProperty(Property):
    @staticmethod
    def unique_key(four_points):
        def perms(four):
            return [four, (*four[1:], four[0]), (*four[2:], *four[:2]), (four[3], *four[:3])]
        return frozenset(perms(four_points) + perms(tuple(reversed(four_points))))

class ConvexQuadrilateralProperty(QuadrilateralProperty):
    """
    Non-degenerate convex quadrilateral
    """
    def __init__(self, quadrilateral):
        assert len(quadrilateral.points) == 4
        self.quadrilateral = quadrilateral
        super().__init__(QuadrilateralProperty.unique_key(quadrilateral.points), set(quadrilateral.points))

    @property
    def __priority__(self):
        return 3

    @property
    def description(self):
        return Comment('$%{polygon:quad}$ is a convex quadrilateral', {'quad': self.quadrilateral})

class SquareProperty(QuadrilateralProperty):
    """
    Square
    """
    @staticmethod
    def unique_key(four_points):
        def perms(four):
            return [four, (*four[1:], four[0]), (*four[2:], *four[:2]), (four[3], *four[:3])]
        return frozenset(perms(four_points) + perms(tuple(reversed(four_points))))

    def __init__(self, square):
        assert len(square.points) == 4
        self.square = square
        super().__init__(QuadrilateralProperty.unique_key(square.points), set(square.points))

    @property
    def __priority__(self):
        return 4

    @property
    def description(self):
        return Comment('$%{polygon:square}$ is a square', {'square': self.square})

class NondegenerateSquareProperty(QuadrilateralProperty):
    """
    Non-degenerate square
    """
    def __init__(self, square):
        assert len(square.points) == 4
        self.square = square
        super().__init__(QuadrilateralProperty.unique_key(square.points), set(square.points))

    @property
    def __priority__(self):
        return 4.5

    @property
    def description(self):
        return Comment('$%{polygon:square}$ is a non-degenerate square', {'square': self.square})

class CentreOfEquilateralTriangleProperty(Property):
    """
    A point is the centre of equilateral triangle
    """
    def __init__(self, centre, triangle):
        self.centre = centre
        self.triangle = triangle
        super().__init__((centre, triangle.symmetric_key), {centre, *self.triangle.points})

    @property
    def __priority__(self):
        return 4.5

    @property
    def description(self):
        return Comment(
            '$%{point:centre}$ is the centre of equilateral $%{triangle:triangle}$',
            {'centre': self.centre, 'triangle': self.triangle}
        )

class OrthocentreOfTriangleProperty(Property):
    """
    A point is the orthocentre of triangle
    """
    def __init__(self, centre, triangle):
        self.centre = centre
        self.triangle = triangle
        super().__init__((centre, triangle.symmetric_key), {centre, *self.triangle.points})

    @property
    def __priority__(self):
        return 4.5

    @property
    def description(self):
        return Comment(
            '$%{point:centre}$ is the orthocentre of $%{triangle:triangle}$',
            {'centre': self.centre, 'triangle': self.triangle}
        )

class AngleKindProperty(Property):
    """
    An angle is acute/obtuse/right
    """
    class Kind(Enum):
        acute  = auto()
        right  = auto()
        obtuse = auto()

        def __str__(self):
            return self.name

    def __init__(self, angle, kind):
        self.angle = angle
        self.kind = kind
        super().__init__(angle, self.angle.point_set)

    def keys(self):
        return [self.angle]

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        if self.kind == AngleKindProperty.Kind.acute:
            pattern = '$%{angle:angle}$ is acute'
        elif self.kind == AngleKindProperty.Kind.obtuse:
            pattern = '$%{angle:angle}$ is obtuse'
        else:
            pattern = '$%{angle:angle}$ is right'
        return Comment(pattern, {'angle': self.angle})

    def compare_values(self, other):
        return self.kind == other.kind

class AngleValueProperty(Property):
    """
    Angle value
    """
    @staticmethod
    def generate(vector0, vector1, value):
        def rev(first, second):
            vec0 = vector0.reversed if first else vector0
            vec1 = vector1.reversed if second else vector1
            return vec0.angle(vec1)

        if vector0.start == vector1.start:
            angles = [(rev(False, False), False)]
        elif vector0.start == vector1.end:
            angles = [(rev(False, True), True)]
        elif vector0.end == vector1.start:
            angles = [(rev(True, False), True)]
        elif vector0.end == vector1.end:
            angles = [(rev(True, True), False)]
        else:
            angles = [
                (rev(False, False), False),
                (rev(False, True), True),
                (rev(True, False), True),
                (rev(True, True), False),
            ]
        for ngl, supplementary in angles:
            yield AngleValueProperty(ngl, 180 - value if supplementary else value)

    def __init__(self, angle, degree):
        assert isinstance(angle, Scene.Angle)
        self.angle = angle
        self.degree = normalize_number(degree)
        super().__init__(angle, self.angle.point_set)

    @property
    def __priority__(self):
        return 1 if self.degree in (0, 90, 180) else 3.5

    def keys(self):
        return [self.angle]

    @property
    def description(self):
        if self.angle.vertex:
            if self.degree == 0:
                return Comment(
                    '$%{point:pt0}$, $%{point:pt1}$ in the same direction from $%{point:vertex}$',
                    {'pt0': self.angle.vectors[0].end, 'pt1': self.angle.vectors[1].end, 'vertex': self.angle.vertex}
                )
            if self.degree == 180:
                return Comment(
                    '$%{point:pt}$ lies inside segment $%{segment:seg}$',
                    {'pt': self.angle.vertex, 'seg': self.angle.vectors[0].end.segment(self.angle.vectors[1].end)}
                )
        else:
            if self.degree == 0:
                return Comment(
                    '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
                    {'vec0': self.angle.vectors[0], 'vec1': self.angle.vectors[1]}
                )
            elif self.degree == 180:
                return Comment(
                    '$%{vector:vec0} \\uparrow\\!\\!\\!\\downarrow %{vector:vec1}$',
                    {'vec0': self.angle.vectors[0], 'vec1': self.angle.vectors[1]}
                )
        return Comment('$%{anglemeasure:ang} = %{degree:deg}$', {'ang': self.angle, 'deg': self.degree})

    def compare_values(self, other):
        return self.degree == other.degree

class MiddleOfSegmentProperty(Property):
    """
    A point is the middle of segment
    """
    def __init__(self, point, segment):
        self.point = point
        self.segment = segment
        super().__init__((point, segment), {point, *segment.points})

    @property
    def __priority__(self):
        return 2

    @property
    def description(self):
        return Comment(
            '$%{point:point}$ is the middle of $%{segment:segment}$',
            {'point': self.point, 'segment': self.segment}
        )

class AngleRatioProperty(Property):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio, same=False):
        assert isinstance(angle0, Scene.Angle)
        assert isinstance(angle1, Scene.Angle)
        # angle0 / angle1 = ratio
        if ratio >= 1:
            self.angle0 = angle0
            self.angle1 = angle1
            self.value = normalize_number(ratio)
        else:
            self.angle0 = angle1
            self.angle1 = angle0
            self.value = divide(1, ratio)
        self.same = same

        super().__init__(frozenset([angle0, angle1]), {*self.angle0.point_set, *self.angle1.point_set})

    def keys(self):
        return [self.angle0, self.angle1]

    @property
    def __priority__(self):
        return 1 if self.same else 3

    @property
    def description(self):
        params = {
            'angle0': self.angle0,
            'angle1': self.angle1,
            'ratio': self.value
        }
        if self.same:
            pattern = '$%{anglemeasure:angle0} \\equiv %{anglemeasure:angle1}$'
        elif self.value == 1:
            pattern = '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$'
        else:
            pattern = '$%{anglemeasure:angle0} = %{multiplier:ratio}\\,%{anglemeasure:angle1}$'
        return Comment(pattern, params)

    def compare_values(self, other):
        return self.value == other.value

class SumOfAnglesProperty(Property):
    """
    Sum of angles is equal to degree
    """
    def __init__(self, *angles, degree):
        self.angles = angles
        self.degree = degree
        points = set()
        for angle in angles:
            points.update(angle.point_set)
        super().__init__(frozenset(angles), points)

    def keys(self):
        return self.angles

    @property
    def __priority__(self):
        return 1 if self.degree == 180 else 3

    @property
    def description(self):
        patterns = ['%{anglemeasure:' + str(i) + '}' for i in range(0, len(self.angles))]
        params = {str(i): angle for i, angle in enumerate(self.angles)}
        params['value'] = self.degree
        return Comment('$' + ' + '.join(patterns) + ' = %{degree:value}$', params)

    def verify(self, placement):
        value = sum(placement.angle(angle) for angle in self.angles)
        return np.fabs(value * 180 / np.pi - self.degree) < 1e-8

    def compare_values(self, other):
        return self.degree == other.degree

class LengthRatioProperty(Property):
    """
    Two non-zero segment lengths ratio
    """
    def __init__(self, segment0, segment1, ratio):
        if ratio >= 1:
            self.segment0 = segment0
            self.segment1 = segment1
            self.value = normalize_number(ratio)
        else:
            self.segment0 = segment1
            self.segment1 = segment0
            self.value = divide(1, ratio)
        super().__init__(frozenset([segment0, segment1]), {*self.segment0.points, *self.segment1.points})

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        return Comment(
            '$|%{segment:seg0}| / |%{segment:seg1}| = %{number:value}$',
            {'seg0': self.segment0, 'seg1': self.segment1, 'value': self.value}
        )

    def compare_values(self, other):
        return self.value == other.value

class ProportionalLengthsProperty(Property):
    """
    Two segment lengths ratio
    """
    def __init__(self, segment0, segment1, ratio):
        if sp.N(ratio) >= 1:
            self.segment0 = segment0
            self.segment1 = segment1
            self.value = normalize_number(ratio)
        else:
            self.segment0 = segment1
            self.segment1 = segment0
            self.value = divide(1, ratio)
        super().__init__(frozenset([segment0, segment1]), {*self.segment0.points, *self.segment1.points})

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        if self.value == 1:
            return Comment('$|%{segment:seg0}| = |%{segment:seg1}|$', {
                'seg0': self.segment0,
                'seg1': self.segment1
            })
        return Comment('$|%{segment:seg0}| = %{multiplier:value}|%{segment:seg1}|$', {
            'seg0': self.segment0,
            'seg1': self.segment1,
            'value': self.value
        })

    def compare_values(self, other):
        if self.value == other.value:
            return True
        return sp.N(self.value) == sp.N(other.value)

class LengthsInequalityProperty(Property):
    """
    Segment is shorter than another one
    """
    @staticmethod
    def unique_key(segment0, segment1):
        return frozenset((segment0, segment1))

    def __init__(self, segment0, segment1):
        self.segments = (segment0, segment1)
        super().__init__(LengthsInequalityProperty.unique_key(segment0, segment1), {*segment0.points, *segment1.points})

    @property
    def description(self):
        return Comment('$|%{segment:seg0}| < |%{segment:seg1}|$', {
            'seg0': self.segments[0], 'seg1': self.segments[1]
        })

    def compare_values(self, other):
        return self.segments[0] == other.segments[0]

class AnglesInequalityProperty(Property):
    """
    Angle is less than another
    """
    @staticmethod
    def unique_key(angle0, angle1):
        return frozenset((angle0, angle1))

    def __init__(self, angle0, angle1):
        self.angles = (angle0, angle1)
        super().__init__(AnglesInequalityProperty.unique_key(angle0, angle1), {*angle0.point_set, *angle1.point_set})

    @property
    def description(self):
        return Comment('$%{anglemeasure:angle0} < %{anglemeasure:angle1}$', {
            'angle0': self.angles[0], 'angle1': self.angles[1]
        })

    def compare_values(self, other):
        return self.angles[0] == other.angles[0]

class EqualLengthProductsProperty(Property):
    """
    Two segment lengths products are equal
    """

    @staticmethod
    def unique_key(segment0, segment1, segment2, segment3):
        return frozenset([
            frozenset([segment0, segment3]),
            frozenset([segment1, segment2])
        ])

    def __init__(self, segment0, segment1, segment2, segment3):
        """
        |segment0| * |segment3| == |segment1| * |segment2|
        """
        self.segments = (segment0, segment1, segment2, segment3)
        super().__init__(EqualLengthProductsProperty.unique_key(segment0, segment1, segment2, segment3), {*segment0.points, *segment1.points, *segment2.points, *segment3.points})

    @property
    def description(self):
        return Comment(
            '$|%{segment:seg0}| * |%{segment:seg3}| = |%{segment:seg1}| * |%{segment:seg2}|$',
            dict(('seg%d' % index, segment) for index, segment in enumerate(self.segments))
        )

class EqualLengthRatiosProperty(Property):
    """
    Two segment lengths ratios are equal
    """

    @staticmethod
    def unique_key(segment0, segment1, segment2, segment3):
        return frozenset([
            (segment0, segment1),
            (segment2, segment3)
        ])

    def __init__(self, segment0, segment1, segment2, segment3):
        """
        |segment0| / |segment1| == |segment2| / |segment3|
        """
        self.segments = (segment0, segment1, segment2, segment3)
        super().__init__(EqualLengthRatiosProperty.unique_key(segment0, segment1, segment2, segment3), {*segment0.points, *segment1.points, *segment2.points, *segment3.points})

    @property
    def description(self):
        return Comment(
            '$|%{segment:seg0}| / |%{segment:seg1}| = |%{segment:seg2}| / |%{segment:seg3}|$',
            dict(('seg%d' % index, segment) for index, segment in enumerate(self.segments))
        )

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(*points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(*points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        super().__init__(frozenset(pairs), {*self.triangle0.points, *self.triangle1.points})

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def __priority__(self):
        return 4

    @property
    def description(self):
        return Comment('$%{triangle:t0} \\sim %{triangle:t1}$', {'t0': self.triangle0, 't1': self.triangle1})

class SimilarNondegenerateTrianglesProperty(Property):
    """
    Two non-degenerate triangles are similar
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(*points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(*points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        super().__init__(frozenset(pairs), {*self.triangle0.points, *self.triangle1.points})

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def __priority__(self):
        return 5

    @property
    def description(self):
        return Comment('$%{triangle:t0}$ and $%{triangle:t1}$ are similar non-degenerate triangles', {'t0': self.triangle0, 't1': self.triangle1})

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(*points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(*points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        super().__init__(frozenset(pairs), {*self.triangle0.points, *self.triangle1.points})

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def __priority__(self):
        return 5

    @property
    def description(self):
        return Comment('$%{triangle:t0} \\cong %{triangle:t1}$', {'t0': self.triangle0, 't1': self.triangle1})

class IsoscelesTriangleProperty(Property):
    """
    Isosceles triangle
    """
    def __init__(self, apex, base):
        self.apex = apex
        self.base = base
        self.triangle = Scene.Triangle(apex, *base.points)
        super().__init__((apex, base), {apex, *base.points})

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def __priority__(self):
        return 4

    @property
    def description(self):
        return Comment(
            '$%{triangle:isosceles}$ is isosceles with apex $%{point:apex}$',
            {'isosceles': self.triangle, 'apex': self.apex}
        )

class Cycle(Figure):
    def __init__(self, pt0, pt1, pt2):
        self.points = (pt0, pt1, pt2)
        self.__key = frozenset([(pt0, pt1, pt2), (pt1, pt2, pt0), (pt2, pt0, pt1)])
        self.__reversed = None

    @property
    def reversed(self):
        if self.__reversed is None:
            self.__reversed = Cycle(*reversed(self.points))
            self.__reversed.__reversed = self
        return self.__reversed

    def __str__(self):
        return '\\circlearrowleft %s %s %s' % self.points

    def __eq__(self, other):
        return other and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

class SameCyclicOrderProperty(Property):
    """
    Two triples of points have the same cyclic order
    """
    def __init__(self, cycle0, cycle1):
        assert isinstance(cycle0, Cycle)
        assert isinstance(cycle1, Cycle)
        self.cycle0 = cycle0
        self.cycle1 = cycle1
        super().__init__(frozenset([cycle0, cycle1]), {*cycle0.points, *cycle1.points})

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return Comment(
            '$%{cycle:cycle0}$ and $%{cycle:cycle1}$ have the same order',
            {'cycle0': self.cycle0, 'cycle1': self.cycle1}
        )

class OrientedAngle(Figure):
    def __init__(self, vertex, pt0, pt1):
        self.vertex = vertex
        self.endpoints = (pt0, pt1)
        self.point_set = {vertex, pt0, pt1}
        self.__key = (vertex, pt0, pt1)

    @property
    def angle(self):
        return self.vertex.angle(*self.endpoints)

    @property
    def cycle(self):
        return Cycle(self.vertex, *self.endpoints)

    def __str__(self):
        return '\\angle %s %s %s' % (self.endpoints[0], self.vertex, self.endpoints[1])

    def __eq__(self, other):
        return other and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

class CongruentOrientedAnglesProperty(Property):
    def __init__(self, angle0, angle1):
        assert isinstance(angle0, OrientedAngle)
        assert isinstance(angle1, OrientedAngle)
        assert angle0 != angle1
        self.angles = (angle0, angle1)
        super().__init__(frozenset([angle0, angle1]), {*angle0.point_set, *angle1.point_set})

    @property
    def __priority__(self):
        return 3

    @property
    def description(self):
        return Comment(
            '$%{orientedangle:angle0}$ and $%{orientedangle:angle1}$ are congruent oriented angles',
            {'angle0': self.angles[0], 'angle1': self.angles[1]}
        )

class IntersectionOfLinesProperty(Property):
    """
    Point is the intersection of two different lines
    """
    def __init__(self, point, segment0, segment1):
        self.point = point
        self.segments = (segment0, segment1)
        super().__init__((point, frozenset([segment0, segment1])), {point, *segment0.points, *segment1.points})

    @property
    def __priority__(self):
        return 2

    @property
    def description(self):
        return Comment(
            '$%{point:point}$ is the intersection of $%{line:line0}$ and $%{line:line1}$',
            {'point': self.point, 'line0': self.segments[0], 'line1': self.segments[1]}
        )

class FootOfPerpendicularProperty(Property):
    """
    Foot of the perpendicular from the given point to the given line
    """
    def __init__(self, foot, point, segment):
        super().__init__((foot, point, segment), {foot, point, *segment.points})
        self.foot = foot
        self.point = point
        self.segment = segment

    @property
    def __priority__(self):
        return 2

    @property
    def description(self):
        return Comment(
            '$%{point:foot}$ is the foot of the perpendicular from $%{point:point}$ to $%{line:line}$',
            {'foot': self.foot, 'point': self.point, 'line': self.segment}
        )
