import itertools

from .util import _comment, divide, good_angles, normalize_number, angle_of, side_of

def keys_for_triangle(triangle, lengths):
    keys = []
    if lengths is None or 3 in lengths:
        keys += [angle_of(triangle, i) for i in range(0, 3)]
    if lengths is None or 2 in lengths:
        keys += [side_of(triangle, i) for i in range(0, 3)]
    return keys

class Property:
    def keys(self):
        return []

    def __str__(self):
        return str(self.description)

class PointsCollinearityProperty(Property):
    """
    [Not] collinear points
    """
    def __init__(self, point0, point1, point2, collinear):
        self.points = (point0, point1, point2)
        self.point_set = frozenset(self.points)
        self.collinear = collinear

    def keys(self, lengths=None):
        return keys_for_triangle(self.points, lengths)

    @property
    def description(self):
        if self.collinear:
            return _comment('Points %s, %s, and %s are collinear', *self.points)
        else:
            return _comment('Points %s, %s, and %s are not collinear', *self.points)

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
        return _comment('%s ↑↑ %s', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, ParallelVectorsProperty) and \
            self.__vector_set == other.__vector_set

    def __hash__(self):
        return hash(ParallelVectorsProperty) + hash(self.__vector_set)

class PerpendicularVectorsProperty(Property):
    """
    Two vectors are perpendicular (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1
        self.__vector_set = frozenset([vector0, vector1])

    def keys(self):
        return [self.vector0.as_segment, self.vector1.as_segment]

    @property
    def description(self):
        return _comment('%s ⟂ %s', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, PerpendicularVectorsProperty) and \
            self.__vector_set == other.__vector_set

    def __hash__(self):
        return hash(PerpendicularVectorsProperty) + hash(self.__vector_set)

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
            return _comment('Points %s and %s are coincident', *self.points)
        else:
            return _comment('Points %s and %s are not coincident', *self.points)

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
            return _comment('%s, %s located on the same side of line %s', *self.points, self.segment)
        else:
            return _comment('%s, %s located on opposite sides of line %s', *self.points, self.segment)

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
        return _comment('%s lies inside %s', self.point, self.angle)

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
    def __init__(self, ABC):
        self.ABC = tuple(ABC)
        self.__point_set = frozenset(self.ABC)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is equilateral', *self.ABC)

    def __eq__(self, other):
        return isinstance(other, EquilateralTriangleProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(EquilateralTriangleProperty) + hash(self.__point_set)

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
                return _comment('%s, %s in the same direction from %s', self.angle.vector0.end, self.angle.vector1.end, self.angle.vertex)
            if self.degree == 180:
                return _comment('%s lies inside segment %s', self.angle.vertex, self.angle.vector0.end.segment(self.angle.vector1.end))
        return _comment('%s = %dº', self.angle, self.degree)

    def __eq__(self, other):
        if not isinstance(other, AngleValueProperty):
            return False
        return self.angle == other.angle

    def __hash__(self):
        return hash(AngleValueProperty) + hash(self.angle)

class AnglesRatioProperty(Property):
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
            return _comment('%s = %s', self.angle0, self.angle1)
        else:
            return _comment('%s = %s %s', self.angle0, self.value, self.angle1)

    def __eq__(self, other):
        return isinstance(other, AnglesRatioProperty) and self.angle_set == other.angle_set

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(AnglesRatioProperty) + hash(self.angle_set)
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
        return _comment('%s + %s = %sº', self.angle0, self.angle1, self.degree)

    def __eq__(self, other):
        return isinstance(other, SumOfAnglesProperty) and self.angle_set == other.angle_set

    def __hash__(self):
        return hash(SumOfAnglesProperty) + hash(self.angle_set)

class RatioOfNonZeroLengthsProperty(Property):
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
        return _comment('|%s| / |%s| = %s', self.segment0, self.segment1, self.value)

    def __eq__(self, other):
        return isinstance(other, RatioOfNonZeroLengthsProperty) and self.segment_set == other.segment_set

    def __hash__(self):
        return hash(RatioOfNonZeroLengthsProperty) + hash(self.segment_set)

class LengthRatioProperty(Property):
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
            return _comment('|%s| = |%s|', self.segment0, self.segment1)
        return _comment('|%s| = %s |%s|', self.segment0, self.value, self.segment1)

    def __eq__(self, other):
        return isinstance(other, LengthRatioProperty) and self.segment_set == other.segment_set

    def __hash__(self):
        return hash(LengthRatioProperty) + hash(self.segment_set)

class PointOnPerpendicularBisectorProperty(Property):
    """
    Point lies on perpendicular bisector of a segment
    """
    def __init__(self, point, segment):
        self.point = point
        self.segment = segment
        self.unique_key = (point, segment)

    @property
    def description(self):
        return _comment('%s lies on the perpendicular bisector of %s', self.point, self.segment)

    def __eq__(self, other):
        return isinstance(other, PointOnPerpendicularBisectorProperty) and self.unique_key == other.unique_key

    def __hash__(self):
        return hash(PointOnPerpendicularBisectorProperty) + hash(self.unique_key)

class EqualLengthRatiosProperty(Property):
    """
    Two segment lengths ratios are equal
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
        self.key = EqualLengthRatiosProperty.unique_key(segment0, segment1, segment2, segment3)

    @property
    def description(self):
        return _comment('|%s| / |%s| = |%s| / |%s|', *self.segments)

    def __eq__(self, other):
        return isinstance(other, EqualLengthRatiosProperty) and self.key == other.key

    def __hash__(self):
        return hash(EqualLengthRatiosProperty) + hash(self.key)

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, ABC, DEF):
        self.ABC = tuple(ABC)
        self.DEF = tuple(DEF)
        pairs = [frozenset([(ABC[i], ABC[j], ABC[k]), (DEF[i], DEF[j], DEF[k])]) for i, j, k in itertools.permutations(range(0, 3), 3)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

    def __eq__(self, other):
        return isinstance(other, SimilarTrianglesProperty) and \
            self.__triangle_set == other.__triangle_set

    def __hash__(self):
        return hash(SimilarTrianglesProperty) + hash(self.__triangle_set)

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, ABC, DEF):
        self.ABC = tuple(ABC)
        self.DEF = tuple(DEF)
        pairs = [frozenset([(ABC[i], ABC[j], ABC[k]), (DEF[i], DEF[j], DEF[k])]) for i, j, k in itertools.permutations(range(0, 3), 3)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s = △ %s %s %s', *self.ABC, *self.DEF)

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

    def keys(self, lengths=None):
        return keys_for_triangle([self.apex, *self.base.points], lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is isosceles (with apex %s)', self.apex, *self.base.points, self.apex)

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
        return _comment('%s and %s have the same order', self.cycle0, self.cycle1)

    def __eq__(self, other):
        return isinstance(other, SameCyclicOrderProperty) and self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)
