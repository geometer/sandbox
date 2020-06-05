from enum import Enum, auto
import itertools

from .figure import Figure
from .scene import Scene
from .util import LazyComment, divide, good_angles, normalize_number, keys_for_triangle, degree_to_string

class Property:
    def __init__(self, property_key):
        self.implications = []
        self.property_key = property_key
        self.__hash = None
        self.__reason = None

    @property
    def reason(self):
        return self.__reason

    @reason.setter
    def reason(self, value):
        if self.__reason:
            for pre in self.__reason.premises:
                pre.implications = [p for p in pre.implications if p is not self]
        while self in value.all_premises:
            # TODO: select the best variant
            for prop in value.all_premises:
                if prop == self:
                    value = prop.reason
        self.__reason = value
        for pre in self.__reason.premises:
            pre.implications.append(self)
        self.fire_premises_change()

    @property
    def priority(self):
        if not hasattr(self, 'rule'):
            return self.__priority__ * 2
        else:
            return self.__priority__ * self.rule.priority()

    @property
    def __priority__(self):
        return 3

    def fire_premises_change(self):
        self.reason.reset_premises()
        for impl in self.implications:
            impl.fire_premises_change()

    def keys(self):
        return []

    def html(self):
        return self.description

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
    Point location relatively to circle
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
        super().__init__(PointAndCircleProperty.unique_key(self.point, self.circle_key))

    def keys(self):
        return self.property_key

    @property
    def description(self):
        # TODO: single circle identifier in comment
        if self.location == PointAndCircleProperty.Kind.inside:
            return LazyComment('%s lies inside the circle through %s, %s, and %s', self.point, *self.circle_key)
        elif self.location == PointAndCircleProperty.Kind.outside:
            return LazyComment('%s lies outside of the circle through %s, %s, and %s', self.point, *self.circle_key)
        elif self.location == PointAndCircleProperty.Kind.on:
            return LazyComment('%s lies on the circle through %s, %s, and %s', self.point, *self.circle_key)
        else:
            raise Exception('location %s is not of type PointAndCircleProperty.Kind' % self.location)

    def compare_values(self, other):
        return self.location == other.location

class CircleCoincidenceProperty(Property):
    """
    Two circles (defined by triples of points) are [not] coincident
    """
    def __init__(self, triple0, triple1, coincident):
        self.circle_keys = (frozenset(triple0), frozenset(triple1))
        super().__init__(frozenset(self.circle_keys))
        self.coincident = coincident

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        # TODO: single circle identifier in comment
        if self.coincident:
            return LazyComment(
                '%s %s %s is the same circle as %s %s %s', *self.circle_keys[0], *self.circle_keys[1]
            )
        else:
            return LazyComment(
                '%s %s %s and %s %s %s are different circles', *self.circle_keys[0], self.circle_keys[1]
            )

    def compare_values(self, other):
        return self.coincident == other.coincident

class ConcyclicPointsProperty(Property):
    """
    Concyclic points
    """
    def __init__(self, *points):
        assert len(points) == 4
        self.points = points
        super().__init__(frozenset(self.points))

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('Points %s, %s, %s, and %s are concyclic', *self.points)

class PointOnLineProperty(Property):
    """
    A point lies [not] on a line
    """
    def __init__(self, point, segment, on_line):
        super().__init__((point, segment))
        self.point = point
        self.segment = segment
        self.on_line = on_line

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment(
            '%s lies on line %s' if self.on_line else '%s does not lie on line %s',
            self.point, self.segment.as_line
        )

    def compare_values(self, other):
        return self.on_line == other.on_line

class LineCoincidenceProperty(Property):
    """
    Two lines (defined by segments) are [not] coincident
    """
    def __init__(self, segment0, segment1, coincident):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments))
        self.coincident = coincident

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        if self.coincident:
            return LazyComment(
                '%s is the same line as %s', self.segments[0].as_line, self.segments[1].as_line
            )
        else:
            return LazyComment(
                '%s and %s are different lines', self.segments[0].as_line, self.segments[1].as_line
            )

    def compare_values(self, other):
        return self.coincident == other.coincident

class PointsCollinearityProperty(Property):
    """
    [Not] collinear points
    """
    def __init__(self, point0, point1, point2, collinear):
        self.points = (point0, point1, point2)
        super().__init__(frozenset(self.points))
        self.collinear = collinear

    @property
    def __priority__(self):
        return 1

    def keys(self, lengths=None):
        return keys_for_triangle(Scene.Triangle(*self.points), lengths)

    @property
    def description(self):
        if self.collinear:
            return LazyComment('Points %s, %s, and %s are collinear', *self.points)
        else:
            return LazyComment('Points %s, %s, and %s are not collinear', *self.points)

    def compare_values(self, other):
        return self.collinear == other.collinear

class ParallelVectorsProperty(Property):
    """
    Two vectors are parallel (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vectors = (vector0, vector1)
        super().__init__(frozenset(self.vectors))

    def keys(self):
        return [self.vectors[0].as_segment, self.vectors[1].as_segment]

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s ↑↑ %s', *self.vectors)

class ParallelSegmentsProperty(Property):
    """
    Two segments are parallel (or at least one of them has zero length)
    """
    def __init__(self, segment0, segment1):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments))

    def keys(self):
        return self.segments

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s ∥ %s', *self.segments)

class PerpendicularSegmentsProperty(Property):
    """
    Two segments are perpendicular (or at least one of them has zero length)
    """
    def __init__(self, segment0, segment1):
        self.segments = (segment0, segment1)
        super().__init__(frozenset(self.segments))

    def keys(self):
        return self.segments

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s ⟂ %s', *self.segments)

class PointsCoincidenceProperty(Property):
    """
    [Not] coincident points
    """
    def __init__(self, point0, point1, coincident):
        self.points = [point0, point1]
        super().__init__(frozenset(self.points))
        self.coincident = coincident

    @property
    def __priority__(self):
        return 3 if self.coincident else 1

    def keys(self):
        return [self.points[0].segment(self.points[1]), *self.points]

    @property
    def description(self):
        if self.coincident:
            return LazyComment('Points %s and %s are coincident', *self.points)
        else:
            return LazyComment('Points %s and %s are not coincident', *self.points)

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
        super().__init__(SameOrOppositeSideProperty.unique_key(segment, point0, point1))

    @property
    def __priority__(self):
        return 1

    def keys(self):
        return [self.segment]

    @property
    def description(self):
        if self.same:
            return LazyComment('%s, %s located on the same side of line %s', *self.points, self.segment.as_line)
        else:
            return LazyComment('%s, %s located on opposite sides of line %s', *self.points, self.segment.as_line)

    def compare_values(self, other):
        return self.same == other.same

class PointInsideAngleProperty(Property):
    """
    A point lies inside an angle
    """
    def __init__(self, point, angle):
        self.point = point
        self.angle = angle
        super().__init__((point, angle))

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s lies inside %s', self.point, self.angle)

    def keys(self):
        return [self.point, self.angle]

class EquilateralTriangleProperty(Property):
    """
    Equilateral triangle
    """
    def __init__(self, points):
        self.triangle = points if isinstance(points, Scene.Triangle) else Scene.Triangle(*points)
        super().__init__(frozenset(self.triangle.points))

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def __priority__(self):
        return 4

    @property
    def description(self):
        return LazyComment('%s is equilateral', self.triangle)

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
        super().__init__(angle)

    def keys(self):
        return [self.angle]

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s is %s', self.angle, self.kind)

    def compare_values(self, other):
        return self.kind == other.kind

class LinearAngleProperty(Property):
    def equation(self, angle_to_expression):
        raise Exception('The method should be implemented in descendants')

class AngleValueProperty(LinearAngleProperty):
    """
    Angle value
    """
    @staticmethod
    def generate(vector0, vector1, value):
        for ngl, complementary in good_angles(vector0, vector1, include_four_point=True):
            yield AngleValueProperty(ngl, 180 - value if complementary else value)

    def __init__(self, angle, degree):
        self.angle = angle
        self.degree = normalize_number(degree)
        super().__init__(angle)

    def equation(self, angle_to_expression):
        return angle_to_expression(self.angle) - self.degree

    @property
    def __priority__(self):
        return 1 if self.degree in (0, 90, 180) else 3.5

    def keys(self):
        return [self.angle]

    @property
    def degree_str(self):
        return degree_to_string(self.degree)

    @property
    def description(self):
        if self.angle.vertex:
            if self.degree == 0:
                return LazyComment('%s, %s in the same direction from %s', self.angle.vectors[0].end, self.angle.vectors[1].end, self.angle.vertex)
            if self.degree == 180:
                return LazyComment('%s lies inside segment %s', self.angle.vertex, self.angle.vectors[0].end.segment(self.angle.vectors[1].end))
        return LazyComment('%s = %s', self.angle, self.degree_str)

    def compare_values(self, other):
        return self.degree == other.degree

class AngleRatioProperty(LinearAngleProperty):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio, same=False):
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

        super().__init__(frozenset([angle0, angle1]))

    def keys(self):
        return [self.angle0, self.angle1]

    def equation(self, angle_to_expression):
        return angle_to_expression(self.angle0) - self.value * angle_to_expression(self.angle1)

    @property
    def __priority__(self):
        return 1 if self.same else 3

    @property
    def description(self):
        if self.same:
            return LazyComment('%s ≡ %s', self.angle0, self.angle1)
        elif self.value == 1:
            return LazyComment('%s = %s', self.angle0, self.angle1)
        else:
            return LazyComment('%s = %s %s', self.angle0, self.value, self.angle1)

    def compare_values(self, other):
        return self.value == other.value

class SumOfThreeAnglesProperty(LinearAngleProperty):
    """
    Sum of three angles is equal to degree
    """
    def __init__(self, angle0, angle1, angle2, degree):
        self.angles = (angle0, angle1, angle2)
        self.degree = degree
        super().__init__(frozenset(self.angles))

    def keys(self):
        return self.angles

    def equation(self, angle_to_expression):
        return angle_to_expression(self.angles[0]) + angle_to_expression(self.angles[1]) + angle_to_expression(self.angles[2]) - self.degree

    @property
    def degree_str(self):
        return degree_to_string(self.degree)

    @property
    def description(self):
        return LazyComment('%s + %s + %s = %s', *self.angles, self.degree_str)

    def compare_values(self, other):
        return self.degree == other.degree

class SumOfTwoAnglesProperty(LinearAngleProperty):
    """
    Sum of two angles is equal to degree
    """
    def __init__(self, angle0, angle1, degree):
        self.angles = (angle0, angle1)
        self.degree = degree
        super().__init__(frozenset([angle0, angle1]))

    def keys(self):
        return self.angles

    def equation(self, angle_to_expression):
        return angle_to_expression(self.angles[0]) + angle_to_expression(self.angles[1]) - self.degree

    @property
    def degree_str(self):
        return degree_to_string(self.degree)

    @property
    def __priority__(self):
        return 1 if self.degree == 180 else 3

    @property
    def description(self):
        return LazyComment('%s + %s = %s', *self.angles, self.degree_str)

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
        super().__init__(frozenset([segment0, segment1]))

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        return LazyComment('|%s| / |%s| = %s', self.segment0, self.segment1, self.value)

    def compare_values(self, other):
        return self.value == other.value

class ProportionalLengthsProperty(Property):
    """
    Two segment lengths ratio
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
        super().__init__(frozenset([segment0, segment1]))

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        if self.value == 1:
            return LazyComment('|%s| = |%s|', self.segment0, self.segment1)
        return LazyComment('|%s| = %s |%s|', self.segment0, self.value, self.segment1)

    def compare_values(self, other):
        return self.value == other.value

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
        super().__init__(EqualLengthProductsProperty.unique_key(segment0, segment1, segment2, segment3))

    @property
    def description(self):
        return LazyComment('|%s| * |%s| = |%s| * |%s|', *[self.segments[i] for i in (0, 3, 1, 2)])

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
        super().__init__(EqualLengthRatiosProperty.unique_key(segment0, segment1, segment2, segment3))

    @property
    def description(self):
        return LazyComment('|%s| / |%s| = |%s| / |%s|', *self.segments)

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(*points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(*points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        super().__init__(frozenset(pairs))

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def __priority__(self):
        return 5

    @property
    def description(self):
        return LazyComment('%s ~ %s', self.triangle0, self.triangle1)

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(*points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(*points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        super().__init__(frozenset(pairs))

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def __priority__(self):
        return 5

    @property
    def description(self):
        return LazyComment('%s = %s', self.triangle0, self.triangle1)

class IsoscelesTriangleProperty(Property):
    """
    Isosceles triangle
    """
    def __init__(self, apex, base):
        self.apex = apex
        self.base = base
        self.triangle = Scene.Triangle(apex, *base.points)
        super().__init__((apex, base))

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def __priority__(self):
        return 4

    @property
    def description(self):
        return LazyComment('%s is isosceles with apex %s', self.triangle, self.apex)

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

    def css_class(self):
        return LazyComment('cyc__%s__%s__%s', *self.points)

    def __str__(self):
        return '↻ %s %s %s' % self.points

    def __eq__(self, other):
        return self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

class SameCyclicOrderProperty(Property):
    """
    Two triples of points have the same cyclic order
    """
    def __init__(self, cycle0, cycle1):
        self.cycle0 = cycle0
        self.cycle1 = cycle1
        super().__init__(frozenset([
            frozenset([cycle0, cycle1]), frozenset([cycle0.reversed, cycle1.reversed])
        ]))

    @property
    def __priority__(self):
        return 1

    @property
    def description(self):
        return LazyComment('%s and %s have the same order', self.cycle0, self.cycle1)
