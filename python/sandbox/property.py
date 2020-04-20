from enum import Enum, auto
import itertools

from .scene import Scene
from .util import LazyComment, divide, good_angles, normalize_number, keys_for_triangle

class Property:
    def keys(self):
        return []

    def __str__(self):
        return str(self.description)

    def compare_values(self, other):
        return True

class PointsCollinearityProperty(Property):
    """
    [Not] collinear points
    """
    def __init__(self, point0, point1, point2, collinear):
        self.points = (point0, point1, point2)
        self.point_set = frozenset(self.points)
        self.collinear = collinear

    def keys(self, lengths=None):
        return keys_for_triangle(Scene.Triangle(self.points), lengths)

    @property
    def description(self):
        if self.collinear:
            return LazyComment('Points %s, %s, and %s are collinear', *self.points)
        else:
            return LazyComment('Points %s, %s, and %s are not collinear', *self.points)

    def compare_values(self, other):
        return self.collinear == other.collinear

    def __eq__(self, other):
        return isinstance(other, PointsCollinearityProperty) and self.point_set == other.point_set

    def __hash__(self):
        return hash(PointsCollinearityProperty) + hash(self.point_set)

class ParallelVectorsProperty(Property):
    """
    Two vectors are parallel (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1
        self.__vector_set = frozenset([vector0, vector1])

    def keys(self):
        return [self.vector0.as_segment, self.vector1.as_segment]

    @property
    def description(self):
        return LazyComment('%s ↑↑ %s', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, ParallelVectorsProperty) and \
            self.__vector_set == other.__vector_set

    def __hash__(self):
        return hash(ParallelVectorsProperty) + hash(self.__vector_set)

class PerpendicularSegmentsProperty(Property):
    """
    Two segments are perpendicular (or at least one of them has zero length)
    """
    def __init__(self, segment0, segment1):
        self.segment0 = segment0
        self.segment1 = segment1
        self.__segment_set = frozenset([segment0, segment1])

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        return LazyComment('%s ⟂ %s', self.segment0, self.segment1)

    def __eq__(self, other):
        return isinstance(other, PerpendicularSegmentsProperty) and \
            self.__segment_set == other.__segment_set

    def __hash__(self):
        return hash(PerpendicularSegmentsProperty) + hash(self.__segment_set)

class PointsCoincidenceProperty(Property):
    """
    [Not] coincident points
    """
    def __init__(self, point0, point1, coincident):
        self.points = [point0, point1]
        self.point_set = frozenset(self.points)
        self.coincident = coincident

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

    def __eq__(self, other):
        return isinstance(other, PointsCoincidenceProperty) and self.point_set == other.point_set

    def __hash__(self):
        return hash(PointsCoincidenceProperty) + hash(self.point_set)

class SameOrOppositeSideProperty(Property):
    """
    Two points on opposite/same sides of a line
    """
    def __init__(self, segment, point0, point1, same):
        self.segment = segment
        self.points = (point0, point1)
        self.same = same
        self.__object_set = frozenset([segment, point0, point1])

    def keys(self):
        return [self.segment]

    @property
    def description(self):
        if self.same:
            return LazyComment('%s, %s located on the same side of line %s', *self.points, self.segment)
        else:
            return LazyComment('%s, %s located on opposite sides of line %s', *self.points, self.segment)

    def compare_values(self, other):
        return self.same == other.same

    def __eq__(self, other):
        return isinstance(other, SameOrOppositeSideProperty) and self.__object_set == other.__object_set

    def __hash__(self):
        return hash(SameOrOppositeSideProperty) + hash(self.__object_set)

class PointInsideAngleProperty(Property):
    """
    Point is inside an angle
    """
    def __init__(self, point, angle):
        self.point = point
        self.angle = angle
        self.__key = (point, angle)

    @property
    def description(self):
        return LazyComment('%s lies inside %s', self.point, self.angle)

    def keys(self):
        return [self.point, self.angle]

    def __eq__(self, other):
        return isinstance(other, PointInsideAngleProperty) and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

class EquilateralTriangleProperty(Property):
    """
    Equilateral triangle
    """
    def __init__(self, points):
        self.triangle = points if isinstance(points, Scene.Triangle) else Scene.Triangle(points)
        self.__point_set = frozenset(self.triangle.points)

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def description(self):
        return LazyComment('%s is equilateral', self.triangle)

    def __eq__(self, other):
        return isinstance(other, EquilateralTriangleProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(EquilateralTriangleProperty) + hash(self.__point_set)

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

    def keys(self):
        return [self.angle]

    @property
    def description(self):
        return LazyComment('%s is %s', self.angle, self.kind)

    def compare_values(self, other):
        return self.kind == other.kind

    def __eq__(self, other):
        return isinstance(other, AngleKindProperty) and self.angle == other.angle

    def __hash__(self):
        return hash(AngleKindProperty) + hash(self.angle)

class AngleValueProperty(Property):
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

    def keys(self):
        return [self.angle]

    @property
    def description(self):
        if self.angle.vertex:
            if self.degree == 0:
                return LazyComment('%s, %s in the same direction from %s', self.angle.vector0.end, self.angle.vector1.end, self.angle.vertex)
            if self.degree == 180:
                return LazyComment('%s lies inside segment %s', self.angle.vertex, self.angle.vector0.end.segment(self.angle.vector1.end))
        return LazyComment('%s = %dº', self.angle, self.degree)

    def compare_values(self, other):
        return self.degree == other.degree

    def __eq__(self, other):
        if not isinstance(other, AngleValueProperty):
            return False
        return self.angle == other.angle

    def __hash__(self):
        return hash(AngleValueProperty) + hash(self.angle)

class AngleRatioProperty(Property):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio):
        # angle0 / angle1 = ratio
        if ratio >= 1:
            self.angle0 = angle0
            self.angle1 = angle1
            self.value = normalize_number(ratio)
        else:
            self.angle0 = angle1
            self.angle1 = angle0
            self.value = divide(1, ratio)

        self.angle_set = frozenset([angle0, angle1])
        self.__hash = None

    def keys(self):
        return [self.angle0, self.angle1]

    @property
    def description(self):
        if self.value == 1:
            return LazyComment('%s = %s', self.angle0, self.angle1)
        else:
            return LazyComment('%s = %s %s', self.angle0, self.value, self.angle1)

    def compare_values(self, other):
        return self.value == other.value

    def __eq__(self, other):
        return isinstance(other, AngleRatioProperty) and self.angle_set == other.angle_set

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(AngleRatioProperty) + hash(self.angle_set)
        return self.__hash

class SumOfAnglesProperty(Property):
    """
    Sum of two angles is equal to degree
    """
    def __init__(self, angle0, angle1, degree):
        self.angle0 = angle0
        self.angle1 = angle1
        self.degree = degree
        self.angle_set = frozenset([angle0, angle1])

    def keys(self):
        return [self.angle0, self.angle1]

    @property
    def description(self):
        return LazyComment('%s + %s = %sº', self.angle0, self.angle1, self.degree)

    def compare_values(self, other):
        return self.degree == other.degree

    def __eq__(self, other):
        return isinstance(other, SumOfAnglesProperty) and self.angle_set == other.angle_set

    def __hash__(self):
        return hash(SumOfAnglesProperty) + hash(self.angle_set)

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
        self.segment_set = frozenset([segment0, segment1])

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        return LazyComment('|%s| / |%s| = %s', self.segment0, self.segment1, self.value)

    def compare_values(self, other):
        return self.value == other.value

    def __eq__(self, other):
        return isinstance(other, LengthRatioProperty) and self.segment_set == other.segment_set

    def __hash__(self):
        return hash(LengthRatioProperty) + hash(self.segment_set)

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
        self.segment_set = frozenset([segment0, segment1])

    def keys(self):
        return [self.segment0, self.segment1]

    @property
    def description(self):
        if self.value == 1:
            return LazyComment('|%s| = |%s|', self.segment0, self.segment1)
        return LazyComment('|%s| = %s |%s|', self.segment0, self.value, self.segment1)

    def compare_values(self, other):
        return self.value == other.value

    def __eq__(self, other):
        return isinstance(other, ProportionalLengthsProperty) and self.segment_set == other.segment_set

    def __hash__(self):
        return hash(ProportionalLengthsProperty) + hash(self.segment_set)

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
        self.segment_set = frozenset(self.segments)
        self.key = EqualLengthProductsProperty.unique_key(segment0, segment1, segment2, segment3)

    @property
    def description(self):
        return LazyComment('|%s| * |%s| = |%s| * |%s|', *[self.segments[i] for i in (0, 3, 1, 2)])

    def __eq__(self, other):
        return isinstance(other, EqualLengthProductsProperty) and self.key == other.key

    def __hash__(self):
        return hash(EqualLengthProductsProperty) + hash(self.key)

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
        self.segment_set = frozenset(self.segments)
        self.key = EqualLengthRatiosProperty.unique_key(segment0, segment1, segment2, segment3)

    @property
    def description(self):
        return LazyComment('|%s| / |%s| = |%s| / |%s|', *self.segments)

    def __eq__(self, other):
        return isinstance(other, EqualLengthRatiosProperty) and self.key == other.key

    def __hash__(self):
        return hash(EqualLengthRatiosProperty) + hash(self.key)

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def description(self):
        return LazyComment('%s ~ %s', self.triangle0, self.triangle1)

    def __eq__(self, other):
        return isinstance(other, SimilarTrianglesProperty) and \
            self.__triangle_set == other.__triangle_set

    def __hash__(self):
        return hash(SimilarTrianglesProperty) + hash(self.__triangle_set)

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, points0, points1):
        self.triangle0 = points0 if isinstance(points0, Scene.Triangle) else Scene.Triangle(points0)
        self.triangle1 = points1 if isinstance(points1, Scene.Triangle) else Scene.Triangle(points1)
        pairs = [frozenset(perms) for perms in zip(self.triangle0.permutations, self.triangle1.permutations)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle0, lengths) + keys_for_triangle(self.triangle1, lengths)

    @property
    def description(self):
        return LazyComment('%s = %s', self.triangle0, self.triangle1)

    def __eq__(self, other):
        return isinstance(other, CongruentTrianglesProperty) and \
            self.__triangle_set == other.__triangle_set

    def __hash__(self):
        return hash(CongruentTrianglesProperty) + hash(self.__triangle_set)

class IsoscelesTriangleProperty(Property):
    """
    Isosceles triangle
    """
    def __init__(self, apex, base):
        self.apex = apex
        self.base = base
        self.triangle = Scene.Triangle((apex, *base.points))

    def keys(self, lengths=None):
        return keys_for_triangle(self.triangle, lengths)

    @property
    def description(self):
        return LazyComment('%s is isosceles (with apex %s)', self.triangle, self.apex)

    def __eq__(self, other):
        return isinstance(other, IsoscelesTriangleProperty) and \
            self.apex == other.apex and self.base == other.base

    def __hash__(self):
        return hash(IsoscelesTriangleProperty) + hash(self.apex) + hash(self.base)

class Cycle:
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
        self.__key = frozenset([
            frozenset([cycle0, cycle1]), frozenset([cycle0.reversed, cycle1.reversed])
        ])

    @property
    def description(self):
        return LazyComment('%s and %s have the same order', self.cycle0, self.cycle1)

    def __eq__(self, other):
        return isinstance(other, SameCyclicOrderProperty) and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)
